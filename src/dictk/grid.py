"""A rectangular collection of points, and batch point tracking across it."""

from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from enum import Enum
from functools import partial

import numpy as np

from dictk import translation
from dictk.correlation import WindowingMethod
from dictk.image import PixelCoordinate


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
