"""A rectangular collection of points, and batch point tracking across it."""

from collections import deque
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from enum import Enum
from functools import partial
from typing import Final

import numpy as np
from scipy.spatial import cKDTree

from dictk import translation, warp
from dictk.correlation import WindowingMethod
from dictk.image import PixelCoordinate, SubpixelCoordinate

# How many nearest points `locate_warp_propagated` links each point to.
# On a rectangular grid, 8 covers the 4 edge neighbors and 4 diagonals.
NEIGHBOR_COUNT: Final[int] = 8

# How many of the start search's best-scoring trials IC-GN refines.
START_SEED_COUNT: Final[int] = 3


class Executor(Enum):
    """Pool type `locate`'s `max_workers` parameter runs on.

    - THREAD: shares memory with the caller, no pickling. Pays a small
      scheduling cost on every task, which does not shrink as task count
      grows.
    - PROCESS: separate memory per worker, needs pickling. Pays a large
      fixed cost once, spawning workers and importing dependencies in
      each -- which then amortizes as task count grows.

    See [Parallelization](../getting_started/parallelization.html) for
    measured trade-offs between the two.
    """

    THREAD = "thread"
    PROCESS = "process"


def _locate_worker(
    args: tuple[PixelCoordinate, PixelCoordinate],
    *,
    reference_image: np.ndarray,
    current_image: np.ndarray,
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
    windowing: WindowingMethod | None,
) -> PixelCoordinate:
    """One point's worth of `translation.locate`, as a single positional
    argument -- `Executor.map` (thread or process) always calls its
    target positionally, one item per iterable, so a keyword-only
    signature is not an option for the function being mapped over.
    Module-level on purpose: `ProcessPoolExecutor` needs a real,
    importable function to hand to spawned workers, not a closure.
    """
    reference_point, search_center = args
    return translation.locate(
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


def _locate_subpixel_worker(
    args: tuple[PixelCoordinate, PixelCoordinate],
    *,
    reference_image: np.ndarray,
    current_image: np.ndarray,
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
    windowing: WindowingMethod | None,
    upsample_factor: int,
) -> SubpixelCoordinate:
    """One point's worth of `translation.locate_subpixel` -- see
    `_locate_worker`'s own docstring for why this is a module-level
    function taking a single positional argument, not a closure."""
    reference_point, search_center = args
    return translation.locate_subpixel(
        reference_image=reference_image,
        current_image=current_image,
        reference_point=reference_point,
        search_center=search_center,
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        search_margin_width=search_margin_width,
        search_margin_height=search_margin_height,
        windowing=windowing,
        upsample_factor=upsample_factor,
    )


def _locate_warp_worker(
    args: tuple[PixelCoordinate, PixelCoordinate],
    *,
    reference_image: np.ndarray,
    current_image: np.ndarray,
    reference_gradients: tuple[np.ndarray, np.ndarray],
    current_coefficients: np.ndarray,
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
    windowing: WindowingMethod | None,
    max_iterations: int,
    tolerance: float,
) -> SubpixelCoordinate:
    """One point's worth of `warp.locate`, reusing gradients and spline
    coefficients computed once per batch -- see `_locate_worker`'s own
    docstring for why this is a module-level function taking a single
    positional argument, not a closure."""
    reference_point, search_center = args
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
    fitted, _znssd, _iterations = warp._refine(
        reference_image=reference_image,
        reference_gradients=reference_gradients,
        current_coefficients=current_coefficients,
        reference_point=reference_point,
        initial_warp=warp._translation_warp(
            reference_point=reference_point, start=start
        ),
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
    return SubpixelCoordinate(
        x=reference_point.x + fitted[0, 2], y=reference_point.y + fitted[1, 2]
    )


def generate(
    *,
    origin: PixelCoordinate,
    count_x: int,
    count_y: int,
    spacing_x: int,
    spacing_y: int,
) -> list[PixelCoordinate]:
    """Generate a rectangular collection of points spanning x and y.

    Points are returned in row-major order (top-left to bottom-right: all
    of row 0 first, then row 1, and so on) -- point `i` sits at the same
    index a later batch tracking call (see `locate`) returns its found
    position at.

    `count_x` and `count_y` need not be equal, and `spacing_x` and
    `spacing_y` need not be equal -- this is a general rectangular
    collection, not a square or uniformly-spaced one.

    `count_x` or `count_y` of exactly `1` is allowed here -- a single
    row or column of points is still a meaningful point-tracking grid on
    its own. That's looser than [`elements`](#elements)'s own
    requirement of `>= 2` along each axis, since forming even 1 finite
    element needs 2 points per axis. The two functions check their own,
    different preconditions independently -- `generate` doesn't know or
    care about elements.

    Args:
        origin: Position of the top-left point, in the source image's
            pixel reference frame.
        count_x: Number of points along x. Must be >= 1.
        count_y: Number of points along y. Must be >= 1.
        spacing_x: Pixel spacing between adjacent points along x.
        spacing_y: Pixel spacing between adjacent points along y.

    Returns:
        A list of `count_x * count_y` `PixelCoordinate`s, in row-major
        order.

    Raises:
        ValueError: If `count_x` or `count_y` is less than 1.
    """
    if count_x < 1:
        raise ValueError(f"count_x {count_x} must be >= 1")
    if count_y < 1:
        raise ValueError(f"count_y {count_y} must be >= 1")

    return [
        PixelCoordinate(x=origin.x + i * spacing_x, y=origin.y + j * spacing_y)
        for j in range(count_y)
        for i in range(count_x)
    ]


def elements(*, count_x: int, count_y: int) -> list[tuple[int, int, int, int]]:
    """Q4 connectivity for the regular `count_x` x `count_y` lattice `generate` produces.

    Each element is one of `generate`'s point grid's unit cells, its 4
    corner nodes given as indices into that same points list -- so
    `[points[i] for i in elements(...)[0]]` are one element's 4 corner
    `PixelCoordinate`s, ready to hand to
    [`dictk.element.gauss_point_green_lagrange_strains`](../api/dictk/element.html#gauss_point_green_lagrange_strains)
    or
    [`dictk.element.gauss_point_log_strains`](../api/dictk/element.html#gauss_point_log_strains).

    Each 4-tuple is `(top_left, top_right, bottom_right, bottom_left)`
    point indices -- the same $N_1$..$N_4$ corner order those functions'
    `shape_functions` convention expects (see [Shape
    Functions](../getting_started/finite_element_method.html#shape-functions)).
    "Top"/"bottom" here use `generate`'s own image-pixel convention (y
    increasing downward, origin at the top-left point) -- not the
    math-style y-up convention `finite_element_method.md`'s figures use,
    where the same 4 points would be called `N1`..`N4`'s "bottom-left,
    bottom-right, top-right, top-left" instead. Only the labels differ
    between the two: the actual point order (start at one corner, then
    +x, then +x and +y together, then +y) is identical either way, and
    that -- not which direction is called "up" -- is what makes it match
    `shape_functions`' expected winding.

    Args:
        count_x: Number of points along x in the source `generate` call.
            Must be >= 2 (at least 2 points make 1 element along x).
        count_y: Number of points along y in the source `generate` call.
            Must be >= 2.

    Returns:
        A list of `(count_x - 1) * (count_y - 1)` 4-tuples, in row-major
        order (all of element row 0 first, then row 1, and so on) --
        matching `generate`'s own point ordering.

    Raises:
        ValueError: If `count_x` or `count_y` is less than 2.
    """
    if count_x < 2:
        raise ValueError(f"count_x {count_x} must be >= 2")
    if count_y < 2:
        raise ValueError(f"count_y {count_y} must be >= 2")

    return [
        (
            j * count_x + i,  # top_left
            j * count_x + i + 1,  # top_right
            (j + 1) * count_x + i + 1,  # bottom_right
            (j + 1) * count_x + i,  # bottom_left
        )
        for j in range(count_y - 1)
        for i in range(count_x - 1)
    ]


def locate(
    *,
    reference_image: np.ndarray,
    current_image: np.ndarray,
    reference_points: Sequence[PixelCoordinate],
    search_centers: Sequence[PixelCoordinate] | None = None,
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
    windowing: WindowingMethod | None = None,
    max_workers: int | None = None,
    executor: Executor = Executor.THREAD,
) -> list[PixelCoordinate]:
    """Batch version of `dictk.translation.locate`: track many points at once.

    Given a collection of `reference_points` (e.g. from `generate`), finds
    each one's position in `current_image` by calling
    [`dictk.translation.locate`](./translation.html#locate) once per point.
    Returns a flat list, index-aligned with `reference_points` -- the same
    row-major order `generate` produces, so point `i`'s found position is
    at index `i` of the result.

    Args:
        reference_image: The reference (undeformed) 2D grayscale image.
        current_image: The current (deformed) 2D grayscale image.
        reference_points: Each point's fixed, known position, in
            `reference_image`'s pixel reference frame.
        search_centers: Where to center each point's search area, in
            `current_image`'s pixel reference frame -- a guess of roughly
            where each `reference_points` entry ended up. If `None`
            (default), each point's own `reference_points` entry is used
            as its own search center, the same reasonable default
            `translation.locate` documents for the single-point case. If
            given, must be the same length as `reference_points`.
        kernel_margin_width: Half each kernel's width, in pixels. Must be
            >= 1.
        kernel_margin_height: Half each kernel's height, in pixels. Must
            be >= 1.
        search_margin_width: Half each search area's width, in pixels.
            Must be greater than `kernel_margin_width`.
        search_margin_height: Half each search area's height, in pixels.
            Must be greater than `kernel_margin_height`.
        windowing: Passed straight through to each per-point
            [`dictk.translation.locate`](./translation.html#locate) call
            -- see its own `windowing` parameter. Default `None` applies
            no windowing to any point, matching this function's original
            behavior exactly.
        max_workers: If given, points are tracked concurrently across
            this many workers instead of one at a time. Default `None`
            stays sequential -- a plain loop, no pool, no overhead --
            matching this function's original behavior exactly. See
            [Parallelization](../getting_started/parallelization.html)
            before setting this: at this book's own teaching scale
            (small kernels and search areas), sequential outperforms
            both pool types at any point count up to 1,000,000, measured.
            Concurrency only pays for itself once each point's own
            correlation is large enough, or point count is large enough
            to amortize `Executor.PROCESS`'s fixed startup cost -- see
            that page for the measured trade-offs.
        executor: Which pool type `max_workers` runs on. Ignored if
            `max_workers` is `None`. Default `Executor.THREAD`.

    Returns:
        Each point's location, in `current_image`'s pixel reference
        frame, in the same order as `reference_points`.

    Raises:
        ValueError: If `search_centers` is given and its length doesn't
            match `reference_points`, `max_workers` is given and less
            than 1, or (from the underlying per-point call) if the
            margin arguments are invalid.
    """
    if search_centers is None:
        search_centers = reference_points
    elif len(search_centers) != len(reference_points):
        raise ValueError(
            f"search_centers length ({len(search_centers)}) must match "
            f"reference_points length ({len(reference_points)})"
        )
    if max_workers is not None and max_workers < 1:
        raise ValueError(f"max_workers {max_workers} must be >= 1")

    if max_workers is None:
        return [
            translation.locate(
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
            for reference_point, search_center in zip(reference_points, search_centers)
        ]

    worker = partial(
        _locate_worker,
        reference_image=reference_image,
        current_image=current_image,
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        search_margin_width=search_margin_width,
        search_margin_height=search_margin_height,
        windowing=windowing,
    )
    executor_cls = (
        ThreadPoolExecutor if executor is Executor.THREAD else ProcessPoolExecutor
    )
    with executor_cls(max_workers=max_workers) as pool:
        return list(pool.map(worker, zip(reference_points, search_centers)))


def locate_subpixel(
    *,
    reference_image: np.ndarray,
    current_image: np.ndarray,
    reference_points: Sequence[PixelCoordinate],
    search_centers: Sequence[PixelCoordinate] | None = None,
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
    windowing: WindowingMethod | None = None,
    upsample_factor: int = 100,
    max_workers: int | None = None,
    executor: Executor = Executor.THREAD,
) -> list[SubpixelCoordinate]:
    """Batch version of `dictk.translation.locate_subpixel`: track many
    points at once, with subpixel refinement.

    Same structure as [`locate`](#locate) -- see its own docstring for
    the full explanation of `search_centers`, `windowing`,
    `max_workers`, and `executor`. The one behavioral difference beyond
    the added `upsample_factor` parameter: each point's found position
    is a [`SubpixelCoordinate`](../image.html#SubpixelCoordinate)
    (generally fractional), not a `PixelCoordinate`, matching
    `translation.locate_subpixel`'s own return type.

    Args:
        reference_image: The reference (undeformed) 2D grayscale image.
        current_image: The current (deformed) 2D grayscale image.
        reference_points: Each point's fixed, known position, in
            `reference_image`'s pixel reference frame.
        search_centers: Where to center each point's search area -- see
            `locate`'s own docstring. If `None` (default), each point's
            own `reference_points` entry is used.
        kernel_margin_width: Half each kernel's width, in pixels. Must
            be >= 1.
        kernel_margin_height: Half each kernel's height, in pixels. Must
            be >= 1.
        search_margin_width: Half each search area's width, in pixels.
            Must be greater than `kernel_margin_width`.
        search_margin_height: Half each search area's height, in pixels.
            Must be greater than `kernel_margin_height`.
        windowing: Passed straight through to each per-point
            [`dictk.translation.locate_subpixel`](../translation.html#locate_subpixel)
            call. Default `None` applies no windowing.
        upsample_factor: Passed straight through to each per-point
            `locate_subpixel` call. Default `100`, matching that
            function's own default. Must be >= 1.
        max_workers: If given, points are tracked concurrently across
            this many workers instead of one at a time -- see `locate`'s
            own docstring for the measured trade-offs.
        executor: Which pool type `max_workers` runs on. Ignored if
            `max_workers` is `None`. Default `Executor.THREAD`.

    Returns:
        Each point's location, in `current_image`'s pixel reference
        frame, generally fractional, in the same order as
        `reference_points`.

    Raises:
        ValueError: If `search_centers` is given and its length doesn't
            match `reference_points`, `max_workers` is given and less
            than 1, or (from the underlying per-point call) if the
            margin or `upsample_factor` arguments are invalid.
    """
    if search_centers is None:
        search_centers = reference_points
    elif len(search_centers) != len(reference_points):
        raise ValueError(
            f"search_centers length ({len(search_centers)}) must match "
            f"reference_points length ({len(reference_points)})"
        )
    if max_workers is not None and max_workers < 1:
        raise ValueError(f"max_workers {max_workers} must be >= 1")

    if max_workers is None:
        return [
            translation.locate_subpixel(
                reference_image=reference_image,
                current_image=current_image,
                reference_point=reference_point,
                search_center=search_center,
                kernel_margin_width=kernel_margin_width,
                kernel_margin_height=kernel_margin_height,
                search_margin_width=search_margin_width,
                search_margin_height=search_margin_height,
                windowing=windowing,
                upsample_factor=upsample_factor,
            )
            for reference_point, search_center in zip(reference_points, search_centers)
        ]

    worker = partial(
        _locate_subpixel_worker,
        reference_image=reference_image,
        current_image=current_image,
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        search_margin_width=search_margin_width,
        search_margin_height=search_margin_height,
        windowing=windowing,
        upsample_factor=upsample_factor,
    )
    executor_cls = (
        ThreadPoolExecutor if executor is Executor.THREAD else ProcessPoolExecutor
    )
    with executor_cls(max_workers=max_workers) as pool:
        return list(pool.map(worker, zip(reference_points, search_centers)))


def locate_warp(
    *,
    reference_image: np.ndarray,
    current_image: np.ndarray,
    reference_points: Sequence[PixelCoordinate],
    search_centers: Sequence[PixelCoordinate] | None = None,
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
    windowing: WindowingMethod | None = None,
    max_iterations: int = 50,
    tolerance: float = 1e-6,
    max_workers: int | None = None,
    executor: Executor = Executor.THREAD,
) -> list[SubpixelCoordinate]:
    """Batch version of `dictk.warp.locate`: track many points at once
    by warping an affine kernel.

    Same structure as [`locate_subpixel`](#locate_subpixel) -- see
    [`locate`](#locate)'s own docstring for the full explanation of
    `search_centers`, `windowing`, `max_workers`, and `executor`.
    `reference_image`'s gradients and `current_image`'s spline
    coefficients are computed once per call, then shared by every point.

    Args:
        reference_image: The reference (undeformed) 2D grayscale image.
        current_image: The current (deformed) 2D grayscale image.
        reference_points: Each point's fixed, known position, in
            `reference_image`'s pixel reference frame.
        search_centers: Where to center each point's whole-pixel search
            -- see `locate`'s own docstring. If `None` (default), each
            point's own `reference_points` entry is used.
        kernel_margin_width: Half each kernel's width, in pixels, not
            counting its center column. Must be >= 1.
        kernel_margin_height: Half each kernel's height, in pixels, not
            counting its center row. Must be >= 1.
        search_margin_width: Half each whole-pixel search area's width,
            in pixels. Must be greater than `kernel_margin_width`.
        search_margin_height: Half each whole-pixel search area's
            height, in pixels. Must be greater than
            `kernel_margin_height`.
        windowing: Passed straight through to each point's whole-pixel
            stage. Default `None` applies no windowing.
        max_iterations: The most IC-GN updates per point. Default `50`.
            Must be >= 1.
        tolerance: IC-GN stops once every warp parameter's update falls
            below this. Default `1e-6`. Must be > 0.
        max_workers: If given, points are tracked concurrently across
            this many workers instead of one at a time.
        executor: Which pool type `max_workers` runs on. Ignored if
            `max_workers` is `None`. Default `Executor.THREAD`.

    Returns:
        Each point's location, in `current_image`'s pixel reference
        frame, generally fractional, in the same order as
        `reference_points`.

    Raises:
        ValueError: If `search_centers` is given but its length doesn't
            match `reference_points`, `max_workers` is less than 1,
            `max_iterations` is less than 1, `tolerance` is not
            positive, or any margin fails `dictk.translation.locate`'s
            own checks.
    """
    if search_centers is None:
        search_centers = reference_points
    elif len(search_centers) != len(reference_points):
        raise ValueError(
            f"search_centers length ({len(search_centers)}) must match "
            f"reference_points length ({len(reference_points)})"
        )
    if max_workers is not None and max_workers < 1:
        raise ValueError(f"max_workers {max_workers} must be >= 1")
    if max_iterations < 1:
        raise ValueError(f"max_iterations {max_iterations} must be >= 1")
    if tolerance <= 0:
        raise ValueError(f"tolerance {tolerance} must be > 0")

    worker = partial(
        _locate_warp_worker,
        reference_image=reference_image,
        current_image=current_image,
        reference_gradients=warp._gradients(reference_image),
        current_coefficients=warp._spline_coefficients(current_image),
        kernel_margin_width=kernel_margin_width,
        kernel_margin_height=kernel_margin_height,
        search_margin_width=search_margin_width,
        search_margin_height=search_margin_height,
        windowing=windowing,
        max_iterations=max_iterations,
        tolerance=tolerance,
    )
    if max_workers is None:
        return [worker(pair) for pair in zip(reference_points, search_centers)]

    executor_cls = (
        ThreadPoolExecutor if executor is Executor.THREAD else ProcessPoolExecutor
    )
    with executor_cls(max_workers=max_workers) as pool:
        return list(pool.map(worker, zip(reference_points, search_centers)))


def locate_warp_propagated(
    *,
    reference_image: np.ndarray,
    current_image: np.ndarray,
    reference_points: Sequence[PixelCoordinate],
    kernel_margin_width: int,
    kernel_margin_height: int,
    search_margin_width: int,
    search_margin_height: int,
    start_gradient_limit: float = 0.3,
    start_gradient_step: float = 0.1,
    max_iterations: int = 50,
    tolerance: float = 1e-6,
) -> list[SubpixelCoordinate]:
    """Track many points by warping an affine kernel, seeding each point
    from an already-fitted neighbor instead of a rigid whole-pixel match.

    [`locate_warp`](#locate_warp) seeds every point's IC-GN fit from
    `dictk.translation.locate`'s rigid, whole-pixel match. Under a large
    stretch or shear, that match can land on the wrong speckles.

    This function searches for a deformed seed at one point only: the
    point nearest the center of `reference_image`. It tries every
    displacement gradient `(u_x, u_y, v_x, v_y)` on a grid from
    `-start_gradient_limit` to `start_gradient_limit` in steps of
    `start_gradient_step`. For each one, it deforms the reference
    kernel and finds its whole-pixel translation by phase correlation.
    IC-GN refines the best-scoring trials, and the fit with the lowest
    ZNSSD becomes the first point's warp. It then visits the remaining points
    breadth-first, through each point's `NEIGHBOR_COUNT` nearest
    points. Each new point starts from the warp of the fitted neighbor
    that reached it: the same displacement gradients, and a translation
    extrapolated across the offset between the two points. See [Seed
    Propagation](../getting_started/seed_propagation.html).

    Points the neighbor links cannot reach from the first point start
    again with the same search, at the unvisited point nearest the
    image center.

    Only those searched points use the search area, centered on each
    one's own reference position. Every other point skips the
    whole-pixel search, so the search margins do not limit how far it
    can move. The fit runs one point at a time, because each seed
    depends on an earlier fit.

    Args:
        reference_image: The reference (undeformed) 2D grayscale image.
        current_image: The current (deformed) 2D grayscale image.
        reference_points: Each point's fixed, known position, in
            `reference_image`'s pixel reference frame. Each point's
            kernel must lie inside `reference_image`.
        kernel_margin_width: Half each kernel's width, in pixels, not
            counting its center column. Must be >= 1.
        kernel_margin_height: Half each kernel's height, in pixels, not
            counting its center row. Must be >= 1.
        search_margin_width: Half the whole-pixel search area's width,
            in pixels, for searched points. Must be greater than
            `kernel_margin_width`. Each searched point's search area
            must lie inside `current_image`.
        search_margin_height: Half the whole-pixel search area's
            height, in pixels, for searched points. Must be greater
            than `kernel_margin_height`.
        start_gradient_limit: The largest displacement gradient the
            start search tries, in each of its four terms. Default
            `0.3`. Must be > 0.
        start_gradient_step: The spacing between tried gradients.
            Default `0.1`, which tries 7 values per term and 2401 in
            all. Must be > 0.
        max_iterations: The most IC-GN updates per point. Default `50`.
            Must be >= 1.
        tolerance: IC-GN stops once every warp parameter's update falls
            below this. Default `1e-6`. Must be > 0.

    Returns:
        Each point's location, in `current_image`'s pixel reference
        frame, generally fractional, in the same order as
        `reference_points`.

    Raises:
        ValueError: If `reference_points` is empty, any point's kernel
            leaves `reference_image`, a searched point's search area
            leaves `current_image`, a margin is too small,
            `start_gradient_limit` or `start_gradient_step` is not
            positive, `max_iterations` is less than 1, or `tolerance`
            is not positive.
    """
    if len(reference_points) == 0:
        raise ValueError("reference_points must not be empty")
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
    if start_gradient_limit <= 0:
        raise ValueError(f"start_gradient_limit {start_gradient_limit} must be > 0")
    if start_gradient_step <= 0:
        raise ValueError(f"start_gradient_step {start_gradient_step} must be > 0")
    if max_iterations < 1:
        raise ValueError(f"max_iterations {max_iterations} must be >= 1")
    if tolerance <= 0:
        raise ValueError(f"tolerance {tolerance} must be > 0")
    height, width = reference_image.shape
    for point in reference_points:
        if not (
            kernel_margin_width <= point.x < width - kernel_margin_width
            and kernel_margin_height <= point.y < height - kernel_margin_height
        ):
            raise ValueError(f"kernel around {point} leaves reference_image")

    positions = np.array([[p.x, p.y] for p in reference_points], dtype=np.float64)
    neighbor_count = min(NEIGHBOR_COUNT + 1, len(reference_points))
    _, neighbors = cKDTree(positions).query(positions, k=neighbor_count)
    neighbors = np.asarray(neighbors).reshape(len(reference_points), -1)
    center = np.array([(width - 1) / 2, (height - 1) / 2])
    by_distance = np.argsort(np.linalg.norm(positions - center, axis=1))

    reference_gradients = warp._gradients(reference_image)
    reference_coefficients = warp._spline_coefficients(reference_image)
    current_coefficients = warp._spline_coefficients(current_image)

    def refined(index, initial_warp):
        return warp._refine(
            reference_image=reference_image,
            reference_gradients=reference_gradients,
            current_coefficients=current_coefficients,
            reference_point=reference_points[index],
            initial_warp=initial_warp,
            kernel_margin_width=kernel_margin_width,
            kernel_margin_height=kernel_margin_height,
            max_iterations=max_iterations,
            tolerance=tolerance,
        )

    warps: list[np.ndarray | None] = [None] * len(reference_points)
    for first in by_distance:
        if warps[first] is not None:
            continue
        point = reference_points[first]
        current_height, current_width = current_image.shape
        if not (
            search_margin_width <= point.x <= current_width - search_margin_width
            and search_margin_height <= point.y <= current_height - search_margin_height
        ):
            raise ValueError(f"search area around {point} leaves current_image")
        seeds = warp._shape_seeds(
            reference_coefficients=reference_coefficients,
            current_image=current_image,
            current_coefficients=current_coefficients,
            reference_point=point,
            kernel_margin_width=kernel_margin_width,
            kernel_margin_height=kernel_margin_height,
            search_margin_width=search_margin_width,
            search_margin_height=search_margin_height,
            gradient_limit=start_gradient_limit,
            gradient_step=start_gradient_step,
            seed_count=START_SEED_COUNT,
        )
        fits = [refined(first, seed) for seed in seeds]
        warps[first] = min(fits, key=lambda fit: fit[1])[0]
        queue = deque([first])
        while queue:
            parent = queue.popleft()
            for child in neighbors[parent]:
                if warps[child] is not None:
                    continue
                parent_warp = warps[parent]
                offset = positions[child] - positions[parent]
                initial_warp = parent_warp.copy()
                initial_warp[:2, 2] += (parent_warp[:2, :2] - np.eye(2)) @ offset
                warps[child] = refined(child, initial_warp)[0]
                queue.append(child)

    return [
        SubpixelCoordinate(x=p.x + w[0, 2], y=p.y + w[1, 2])
        for p, w in zip(reference_points, warps)
    ]
