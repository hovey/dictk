"""A rectangular collection of points, and batch point tracking across it."""

from collections.abc import Sequence

import numpy as np

from dictk import translation
from dictk.correlation import WindowingMethod
from dictk.image import PixelCoordinate


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

    Returns:
        Each point's location, in `current_image`'s pixel reference
        frame, in the same order as `reference_points`.

    Raises:
        ValueError: If `search_centers` is given and its length doesn't
            match `reference_points`, or (from the underlying per-point
            call) if the margin arguments are invalid.
    """
    if search_centers is None:
        search_centers = reference_points
    elif len(search_centers) != len(reference_points):
        raise ValueError(
            f"search_centers length ({len(search_centers)}) must match "
            f"reference_points length ({len(reference_points)})"
        )

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
