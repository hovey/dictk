"""Image I/O, grayscale conversion, combination, and inspection utilities."""

import base64
import importlib.resources
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

import imageio.v3 as iio
import numpy as np
from matplotlib import patches
from matplotlib import patheffects
from matplotlib import pyplot as plt
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import zoom


class PixelCoordinate(NamedTuple):
    """A pixel location in an image's reference frame.

    Attributes:
        x: Horizontal pixel coordinate, increasing left to right.
        y: Vertical pixel coordinate, increasing top to bottom.
    """

    x: int
    y: int


# Shared figure scale (pixels of image data per inch) for
# subimage_bounds_plot() and subimage_plot(), so each saved figure's size
# is proportional to its actual pixel content rather than a fixed default
# figure size -- letting the two be visually compared for relative size
# instead of both rendering at roughly the same size regardless of how
# many pixels each actually covers.
_FIGURE_PIXELS_PER_INCH = 100


def subimage(
    *, image: np.ndarray, origin: PixelCoordinate, width: int, height: int
) -> np.ndarray:
    """Extract a width x height crop of `image` with its top-left corner at `origin`.

    `origin` is expressed in `image`'s own pixel reference frame (`image`'s
    top-left corner is `(0, 0)`) and may lie partially or entirely outside
    `image`'s bounds. Wherever the requested region doesn't overlap
    `image`, the corresponding output pixels are zero (black) rather than
    raising an error — so a subimage straddling an edge, or lying
    completely outside `image`, is always a valid, well-shaped result.

    Args:
        image: Source 2D grayscale image array.
        origin: Top-left corner of the region to extract, in `image`'s
            pixel reference frame.
        width: Width of the extracted region in pixels. Must be >= 1.
        height: Height of the extracted region in pixels. Must be >= 1.

    Returns:
        A 2D array of shape (height, width), same dtype as `image`.

    Raises:
        ValueError: If `image` is not 2D, or width or height is less than 1.
    """
    if image.ndim != 2:
        raise ValueError(f"image must be 2D, got shape {image.shape}")
    if width < 1:
        raise ValueError(f"width {width} must be >= 1")
    if height < 1:
        raise ValueError(f"height {height} must be >= 1")

    image_height, image_width = image.shape
    result = np.zeros((height, width), dtype=image.dtype)

    src_x_start = max(origin.x, 0)
    src_y_start = max(origin.y, 0)
    src_x_end = min(origin.x + width, image_width)
    src_y_end = min(origin.y + height, image_height)

    if src_x_start >= src_x_end or src_y_start >= src_y_end:
        return result  # requested region doesn't overlap image at all

    dst_x_start = src_x_start - origin.x
    dst_y_start = src_y_start - origin.y
    dst_x_end = dst_x_start + (src_x_end - src_x_start)
    dst_y_end = dst_y_start + (src_y_end - src_y_start)

    result[dst_y_start:dst_y_end, dst_x_start:dst_x_end] = image[
        src_y_start:src_y_end, src_x_start:src_x_end
    ]
    return result


def subimage_bounds_plot(
    *,
    image: np.ndarray,
    origin: PixelCoordinate,
    width: int,
    height: int,
    path: Path,
    dpi: int = 300,
) -> None:
    """Save a figure overlaying a source image's bounds and a subimage region.

    Draws `image`'s own bounds in blue and the requested `origin`/`width`/
    `height` region in red, on top of `image` itself — including cases
    where the red region extends partially or completely outside the blue
    one, to visualize what `subimage()` would crop from. An `'o'` marker
    is also drawn at each rectangle's own origin: blue at `(0, 0)` for
    `image`, red at `origin` for the subimage — both in `image`'s pixel
    reference frame.

    Args:
        image: Source 2D grayscale image array.
        origin: Top-left corner of the region, in `image`'s pixel
            reference frame; see `subimage()`.
        width: Width of the region in pixels. Must be >= 1.
        height: Height of the region in pixels. Must be >= 1.
        path: Output file path for the figure; format is inferred from
            the extension by matplotlib's savefig (e.g. .png), not
            dictk's own write/write_svg.
        dpi: Resolution of the saved figure.

    Raises:
        ValueError: If width or height is less than 1.
    """
    if width < 1:
        raise ValueError(f"width {width} must be >= 1")
    if height < 1:
        raise ValueError(f"height {height} must be >= 1")

    image_height, image_width = image.shape

    margin = max(width, height, image_width, image_height) * 0.05
    x_min = min(0, origin.x) - margin
    x_max = max(image_width, origin.x + width) + margin
    y_min = min(0, origin.y) - margin
    y_max = max(image_height, origin.y + height) + margin

    figsize = (
        (x_max - x_min) / _FIGURE_PIXELS_PER_INCH,
        (y_max - y_min) / _FIGURE_PIXELS_PER_INCH,
    )
    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(
        image, cmap="gray", origin="upper", extent=(0, image_width, image_height, 0)
    )

    ax.add_patch(
        patches.Rectangle(
            (0, 0),
            image_width,
            image_height,
            edgecolor="blue",
            facecolor="none",
            linewidth=1.5,
            label="source image",
        )
    )
    ax.add_patch(
        patches.Rectangle(
            (origin.x, origin.y),
            width,
            height,
            edgecolor="red",
            facecolor="none",
            linewidth=1.5,
            label="subimage",
        )
    )
    ax.plot(0, 0, marker="o", color="blue", markersize=6)
    ax.plot(origin.x, origin.y, marker="o", color="red", markersize=6)

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_max, y_min)  # inverted: image y increases downward

    ax.set_xlabel("x (pixels)")
    ax.set_ylabel("y (pixels)")
    # Legend placed fully outside the axes (not just an "upper right"-style
    # corner) so it never overlaps the source or subimage rectangles,
    # regardless of how much of the frame they fill; bbox_inches="tight"
    # on save keeps it from being clipped off the saved figure.
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8)
    ax.set_title(f"subimage bounds: origin=({origin.x}, {origin.y}), {width}x{height}")

    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def subimage_plot(
    *,
    image: np.ndarray,
    origin: PixelCoordinate,
    width: int,
    height: int,
    path: Path,
    dpi: int = 300,
) -> None:
    """Save a figure of the subimage itself, in its own local reference frame.

    Extracts the `width` x `height` region at `origin` (via `subimage()`)
    and plots just that result, labeled with its own local pixel
    coordinates — `(0, 0)` at its own top-left corner — rather than
    `image`'s coordinates. An `'o'` marker is drawn at that local origin
    `(0, 0)`, matching the red origin marker `subimage_bounds_plot()`
    draws at the same subimage in `image`'s reference frame. Unlike
    `subimage_bounds_plot()`, which shows where the region falls relative
    to `image`, this shows what the extracted result actually looks like,
    including any zero (black) padding from parts of the region that fell
    outside `image`.

    Args:
        image: Source 2D grayscale image array.
        origin: Top-left corner of the region, in `image`'s pixel
            reference frame; see `subimage()`.
        width: Width of the region in pixels. Must be >= 1.
        height: Height of the region in pixels. Must be >= 1.
        path: Output file path for the figure; format is inferred from
            the extension by matplotlib's savefig (e.g. .png), not
            dictk's own write/write_svg.
        dpi: Resolution of the saved figure.

    Raises:
        ValueError: If width or height is less than 1.
    """
    region = subimage(image=image, origin=origin, width=width, height=height)

    # Same margin approach as subimage_bounds_plot(), so the red border
    # gets the same small breathing room from the figure edge instead of
    # sitting flush against it.
    margin = max(width, height) * 0.05
    x_min, x_max = -margin, width + margin
    y_min, y_max = -margin, height + margin

    figsize = (
        (x_max - x_min) / _FIGURE_PIXELS_PER_INCH,
        (y_max - y_min) / _FIGURE_PIXELS_PER_INCH,
    )
    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(region, cmap="gray", origin="upper", extent=(0, width, height, 0))
    ax.add_patch(
        patches.Rectangle(
            (0, 0),
            width,
            height,
            edgecolor="red",
            facecolor="none",
            linewidth=1.5,
        )
    )
    ax.plot(0, 0, marker="o", color="red", markersize=6)

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_max, y_min)  # inverted: image y increases downward

    ax.set_xlabel("x (pixels)")
    ax.set_ylabel("y (pixels)")

    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def subimage_comparison_plot(
    *,
    image: np.ndarray,
    origin: PixelCoordinate,
    width: int,
    height: int,
    path: Path,
    point: PixelCoordinate | None = None,
    point_color: str = "gold",
    point_label: str | None = None,
    subimage_label: str | None = None,
    color: str = "red",
    origin_label: str | None = None,
    source_origin_label: str | None = None,
    dpi: int = 300,
) -> None:
    """Save a side-by-side comparison of a subimage's placement and its extraction.

    The left panel matches `subimage_bounds_plot()`: `image`'s bounds in
    blue, the requested region in `color` (red by default), with an `'o'`
    marker at each rectangle's own origin. The right panel shows the
    extracted subimage (via `subimage()`) with a `color` border and
    origin marker, in its own local reference frame — but drawn using the
    *same* axis limits as the left panel, rather than being cropped or
    zoomed to the subimage's own size the way `subimage_plot()` is. That
    shared scale is what makes the two boxes render at identical size by
    construction — same data units per pixel in both panels — rather than
    approximating it by sizing each panel's figure independently around
    its own content.

    Args:
        image: Source 2D grayscale image array.
        origin: Top-left corner of the region, in `image`'s pixel
            reference frame; see `subimage()`.
        width: Width of the region in pixels. Must be >= 1.
        height: Height of the region in pixels. Must be >= 1.
        path: Output file path for the figure; format is inferred from
            the extension by matplotlib's savefig (e.g. .png), not
            dictk's own write/write_svg.
        point: An optional point of interest, in `image`'s pixel reference
            frame, marked with a `point_color` dot on both panels — at
            `point` itself on the left, and at `point` translated into
            the subimage's own local frame (`point` minus `origin`) on
            the right, since that's the same physical point expressed in
            each panel's own coordinates.
        point_color: Matplotlib color name for `point`'s marker. Ignored
            if `point` isn't given.
        point_label: An optional short text label (e.g. `"P"`) drawn next
            to `point`'s marker, on both panels. Ignored if `point` isn't
            given.
        subimage_label: An optional short label identifying what this
            subimage represents (e.g. `"kernel"`), appended to the right
            panel's "subimage" title as "subimage (label)". Left as-is
            ("subimage") when not given.
        color: Matplotlib color name for the subimage's bounding box and
            origin marker, on both panels.
        origin_label: An optional short text label (e.g. `"K"`) drawn
            next to the subimage's own origin marker, on both panels.
        source_origin_label: An optional short text label (e.g. `"O"`)
            drawn next to `image`'s own origin marker (the blue dot),
            on the left panel only -- the right panel has no equivalent
            marker for it.
        dpi: Resolution of the saved figure.

    Raises:
        ValueError: If width or height is less than 1.
    """
    if width < 1:
        raise ValueError(f"width {width} must be >= 1")
    if height < 1:
        raise ValueError(f"height {height} must be >= 1")

    region = subimage(image=image, origin=origin, width=width, height=height)
    image_height, image_width = image.shape

    margin = max(width, height, image_width, image_height) * 0.05
    if source_origin_label is not None or origin_label is not None:
        # source_origin_label/origin_label sit just up-right of a marker at
        # (0, 0) -- the top-left corner of the panel's own content -- so
        # "up" lands in this margin, above the panel title. The default
        # margin (5% of the content) can be too thin to fit a 12pt label
        # there without touching the title, regardless of image size, so
        # widen it enough to fit one when either label is in use.
        margin = max(margin, (12 * 2.2) / 72 * _FIGURE_PIXELS_PER_INCH)
    x_min = min(0, origin.x) - margin
    x_max = max(image_width, origin.x + width) + margin
    y_min = min(0, origin.y) - margin
    y_max = max(image_height, origin.y + height) + margin

    # Small up-right offset for marker labels, so label text doesn't sit
    # directly on top of its own marker.
    label_offset = max(image_width, image_height) * 0.03
    # A thin white outline keeps every marker label legible against
    # whatever's directly behind it in the image content.
    label_outline = [patheffects.withStroke(linewidth=1, foreground="white")]

    panel_width = (x_max - x_min) / _FIGURE_PIXELS_PER_INCH
    panel_height = (y_max - y_min) / _FIGURE_PIXELS_PER_INCH
    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=(panel_width * 2, panel_height), constrained_layout=True
    )

    ax_left.imshow(
        image, cmap="gray", origin="upper", extent=(0, image_width, image_height, 0)
    )
    ax_left.add_patch(
        patches.Rectangle(
            (0, 0),
            image_width,
            image_height,
            edgecolor="blue",
            facecolor="none",
            linewidth=1.5,
        )
    )
    ax_left.add_patch(
        patches.Rectangle(
            (origin.x, origin.y),
            width,
            height,
            edgecolor=color,
            facecolor="none",
            linewidth=1.5,
        )
    )
    ax_left.plot(0, 0, marker="o", color="blue", markersize=6)
    ax_left.plot(origin.x, origin.y, marker="o", color=color, markersize=6)
    if point is not None:
        ax_left.plot(point.x, point.y, marker="o", color=point_color, markersize=6)
    if source_origin_label is not None:
        ax_left.text(
            label_offset,
            -label_offset,
            source_origin_label,
            color="blue",
            fontsize=12,
            path_effects=label_outline,
        )
    if origin_label is not None:
        ax_left.text(
            origin.x + label_offset,
            origin.y - label_offset,
            origin_label,
            color=color,
            fontsize=12,
            path_effects=label_outline,
        )
    if point is not None and point_label is not None:
        ax_left.text(
            point.x + label_offset,
            point.y - label_offset,
            point_label,
            color=point_color,
            fontsize=12,
            path_effects=label_outline,
        )
    ax_left.set_xlim(x_min, x_max)
    ax_left.set_ylim(y_max, y_min)  # inverted: image y increases downward
    ax_left.set_xlabel("x (pixels)")
    ax_left.set_ylabel("y (pixels)")
    ax_left.set_title("source image + subimage")

    ax_right.imshow(region, cmap="gray", origin="upper", extent=(0, width, height, 0))
    ax_right.add_patch(
        patches.Rectangle(
            (0, 0),
            width,
            height,
            edgecolor=color,
            facecolor="none",
            linewidth=1.5,
        )
    )
    ax_right.plot(0, 0, marker="o", color=color, markersize=6)
    if point is not None:
        ax_right.plot(
            point.x - origin.x, point.y - origin.y, marker="o", color=point_color, markersize=6
        )
    if origin_label is not None:
        ax_right.text(
            label_offset, -label_offset, origin_label, color=color, fontsize=12, path_effects=label_outline
        )
    if point is not None and point_label is not None:
        ax_right.text(
            point.x - origin.x + label_offset,
            point.y - origin.y - label_offset,
            point_label,
            color=point_color,
            fontsize=12,
            path_effects=label_outline,
        )
    # Same limits as ax_left, not the subimage's own tight size -- this is
    # the whole point: identical data-units-per-pixel in both panels.
    ax_right.set_xlim(x_min, x_max)
    ax_right.set_ylim(y_max, y_min)
    ax_right.set_xlabel("x (pixels)")
    ax_right.set_ylabel("y (pixels)")
    ax_right.set_title(
        f"subimage ({subimage_label})" if subimage_label is not None else "subimage"
    )

    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


class ArrowAnnotation(NamedTuple):
    """A labeled, colored arrow to overlay on an image, from `tail` to `head`.

    Attributes:
        tail: Arrow's starting point, in the image's pixel reference frame.
        head: Arrow's ending point, in the image's pixel reference frame.
        color: Matplotlib color name for the arrow and its legend entry.
        label: Legend label for the arrow.
    """

    tail: PixelCoordinate
    head: PixelCoordinate
    color: str
    label: str


class BoxAnnotation(NamedTuple):
    """A labeled, colored rectangle (with an origin marker) to overlay on an image.

    Attributes:
        origin: Top-left corner of the rectangle, in the image's pixel
            reference frame; see `subimage()`.
        width: Width of the rectangle in pixels.
        height: Height of the rectangle in pixels.
        color: Matplotlib color name for the rectangle, its origin
            marker, and its legend entry.
        label: Legend label for the rectangle.
    """

    origin: PixelCoordinate
    width: int
    height: int
    color: str
    label: str


class PointAnnotation(NamedTuple):
    """A short colored text label to draw at a point on an image, with no marker of its own.

    Meant for labeling a point that already has its own marker drawn some
    other way (e.g. an `ArrowAnnotation`'s head/tail, or a `BoxAnnotation`'s
    origin) with a short symbol, like `"$P$"`.

    Attributes:
        position: Location of the label, in the image's pixel reference frame.
        label: Short text to draw (e.g. `"$P$"`); LaTeX math (`$...$`) is
            rendered via matplotlib's built-in mathtext.
        color: Matplotlib color name for the label text.
    """

    position: PixelCoordinate
    label: str
    color: str


def point_plot(
    *,
    image: np.ndarray,
    arrows: Sequence[ArrowAnnotation],
    boxes: Sequence[BoxAnnotation] = (),
    points: Sequence[PointAnnotation] = (),
    legend: bool = True,
    path: Path,
    dpi: int = 300,
) -> None:
    """Save a figure overlaying one or more labeled arrows (and boxes) on `image`.

    Each `ArrowAnnotation` draws a straight arrow from `tail` to `head`, in
    `image`'s own pixel reference frame — e.g. from the origin `(0, 0)` to a
    point of interest, or between two points to show a displacement. Each
    `BoxAnnotation` draws a rectangle with an `'o'` marker at its own
    origin, layered behind the arrows but in front of `image` -- e.g. to
    show where a kernel or search area sits on a figure that's mainly
    about the arrows drawn on top of it. Each `PointAnnotation` draws a
    short text label (with a thin white outline, so it stays legible
    against the image) next to a point already marked some other way.

    Args:
        image: Source 2D grayscale image array.
        arrows: One or more arrows to overlay, each with its own color and
            legend label.
        boxes: Zero or more rectangles to overlay underneath the arrows,
            each with its own color and legend label.
        points: Zero or more short text labels to draw, each next to a
            point already marked by an arrow or box elsewhere in the
            figure.
        legend: Whether to draw the arrow/box legend. Set to False when
            the arrow/box labels are already explained elsewhere (e.g. a
            figure caption) and would just clutter the figure.
        path: Output file path for the figure; format is inferred from the
            extension by matplotlib's savefig (e.g. .png), not dictk's own
            write/write_svg.
        dpi: Resolution of the saved figure.

    Raises:
        ValueError: If `arrows` is empty.
    """
    if not arrows:
        raise ValueError("arrows must not be empty")

    image_height, image_width = image.shape

    endpoints_x = [pt.x for arrow in arrows for pt in (arrow.tail, arrow.head)]
    endpoints_y = [pt.y for arrow in arrows for pt in (arrow.tail, arrow.head)]
    for box in boxes:
        endpoints_x += [box.origin.x, box.origin.x + box.width]
        endpoints_y += [box.origin.y, box.origin.y + box.height]
    endpoints_x += [point.position.x for point in points]
    endpoints_y += [point.position.y for point in points]
    margin = max(image_width, image_height) * 0.05
    if points:
        # Point labels sit just up-right of their marker, so a point at
        # (0, 0) -- the image's own top-left corner -- would have its
        # label land in this margin, above the title. The default margin
        # (5% of the image) can be too thin to fit a 12pt label there
        # regardless of image size, so widen it enough to fit one.
        margin = max(margin, (12 * 2.2) / 72 * _FIGURE_PIXELS_PER_INCH)
    x_min = min(0, *endpoints_x) - margin
    x_max = max(image_width, *endpoints_x) + margin
    y_min = min(0, *endpoints_y) - margin
    y_max = max(image_height, *endpoints_y) + margin

    # Small up-right offset for point labels, so label text doesn't sit
    # directly on top of its own marker.
    label_offset = max(image_width, image_height) * 0.03
    label_outline = [patheffects.withStroke(linewidth=1, foreground="white")]

    figsize = (
        (x_max - x_min) / _FIGURE_PIXELS_PER_INCH,
        (y_max - y_min) / _FIGURE_PIXELS_PER_INCH,
    )
    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(
        image, cmap="gray", origin="upper", extent=(0, image_width, image_height, 0)
    )

    for box in boxes:
        ax.add_patch(
            patches.Rectangle(
                (box.origin.x, box.origin.y),
                box.width,
                box.height,
                edgecolor=box.color,
                facecolor="none",
                linewidth=1.5,
            )
        )
        ax.plot(box.origin.x, box.origin.y, marker="o", color=box.color, markersize=6)

    for arrow in arrows:
        ax.annotate(
            "",
            xy=(arrow.head.x, arrow.head.y),
            xytext=(arrow.tail.x, arrow.tail.y),
            arrowprops={
                "color": arrow.color,
                "width": 1.5,
                "headwidth": 8,
                "shrink": 0,
            },
        )

    # Drawn last (on top of the arrows), so a label sitting where an arrow
    # starts or ends doesn't get partly covered by the arrow itself.
    for point in points:
        ax.text(
            point.position.x + label_offset,
            point.position.y - label_offset,
            point.label,
            color=point.color,
            fontsize=12,
            path_effects=label_outline,
        )
    # ax.annotate's arrows don't register with the legend on their own, so
    # proxy line handles stand in for each arrow's (and box's) color/label.
    handles = [
        plt.Line2D([0], [0], color=arrow.color, lw=1.5, label=arrow.label)
        for arrow in arrows
    ] + [
        patches.Patch(edgecolor=box.color, facecolor="none", label=box.label)
        for box in boxes
    ]

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_max, y_min)  # inverted: image y increases downward
    ax.set_xlabel("x (pixels)")
    ax.set_ylabel("y (pixels)")
    if legend:
        # Same fully-outside legend placement as subimage_bounds_plot(), so
        # it never overlaps the image regardless of arrow placement.
        ax.legend(
            handles=handles, loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=8
        )

    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def reference_frame_plot(*, image: np.ndarray, path: Path, dpi: int = 300) -> None:
    """Save a side-by-side figure contrasting `image` with its reference frame made explicit.

    Left panel: `image` alone, with no annotation — no axes box, ticks, or
    labels either — a reminder that a pixel reference frame is always
    implicitly present, even when nothing is drawn to show it. Right
    panel: the same `image`, with its bounds outlined in blue and a blue
    'o' marker at its origin `(0, 0)` (top-left corner) — the same style
    `subimage_bounds_plot()` uses for a source image — plus a red arrow
    along the x-axis and a green arrow along the y-axis, both starting
    from that origin, making the top-left-origin, y-increases-downward
    pixel convention used throughout this codebase explicit, labeled with
    the calligraphic frame symbol "F" just above and to the left of the
    origin marker. The "x"/"y" axis labels sit in the margin outside the
    blue frame, rather than on top of it, so they don't overlap its
    border.

    Args:
        image: Source 2D grayscale image array.
        path: Output file path for the figure; format is inferred from
            the extension by matplotlib's savefig (e.g. .png), not
            dictk's own write/write_svg.
        dpi: Resolution of the saved figure.
    """
    image_height, image_width = image.shape
    axis_length = min(image_width, image_height) * 0.2

    margin = max(image_width, image_height) * 0.05
    # The "x"/"y" labels need enough margin to sit clear of both the blue
    # frame and the axes spine; the label's rendered size only depends on
    # its font size and the data-units-per-inch scale figsize is built
    # from, not on image size, so a small image's default margin (5% of
    # its own dimensions) can otherwise be too little to fit it.
    label_font_size = 12
    frame_label_font_size = 14
    min_margin_for_labels = (
        max(label_font_size, frame_label_font_size) * 2.2 / 72 * _FIGURE_PIXELS_PER_INCH
    )
    margin = max(margin, min_margin_for_labels)

    x_min, x_max = -margin, image_width + margin
    y_min, y_max = -margin, image_height + margin

    panel_width = (x_max - x_min) / _FIGURE_PIXELS_PER_INCH
    panel_height = (y_max - y_min) / _FIGURE_PIXELS_PER_INCH
    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=(panel_width * 2, panel_height), constrained_layout=True
    )

    for ax in (ax_left, ax_right):
        ax.imshow(
            image,
            cmap="gray",
            origin="upper",
            extent=(0, image_width, image_height, 0),
        )
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_max, y_min)  # inverted: image y increases downward

    ax_left.set_title("image")
    ax_left.axis("off")

    ax_right.set_xlabel("x (pixels)")
    ax_right.set_ylabel("y (pixels)")

    ax_right.add_patch(
        patches.Rectangle(
            (0, 0),
            image_width,
            image_height,
            edgecolor="blue",
            facecolor="none",
            linewidth=1.5,
        )
    )
    ax_right.plot(0, 0, marker="o", color="blue", markersize=8)

    # Frame label sits just above and to the left of the origin marker,
    # in the empty diagonal corner the x-/y-axis arrows leave untouched.
    frame_label_offset = margin * 0.35
    ax_right.text(
        -frame_label_offset,
        -frame_label_offset,
        r"$\mathcal{F}$",
        color="blue",
        fontsize=frame_label_font_size,
        ha="right",
        va="bottom",
    )

    # Labels sit centered in the margin strip between the blue frame and
    # the axes spine, rather than at the arrowhead itself, so they don't
    # touch either (the arrows run flush along the top/left edges of the
    # frame's border).
    label_offset = margin / 2
    for axis_head, label_pos, color, label, ha, va in (
        ((axis_length, 0), (axis_length, -label_offset), "red", "x", "center", "bottom"),
        ((0, axis_length), (-label_offset, axis_length), "green", "y", "right", "center"),
    ):
        ax_right.annotate(
            "",
            xy=axis_head,
            xytext=(0, 0),
            arrowprops={"color": color, "width": 1.5, "headwidth": 8, "shrink": 0},
        )
        ax_right.text(*label_pos, label, color=color, fontsize=label_font_size, ha=ha, va=va)

    ax_right.set_title("reference frame")

    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def checkerboard(
    *, width: int, height: int, count_x: int = 8, count_y: int = 8
) -> np.ndarray:
    """Generate a black-and-white checkerboard test image.

    Same parameters and pixel values as the `dictk checkerboard` CLI
    command, minus the file write — see the `dictk` package docstring for
    why the API layer stops at the array. count_x and count_y are named for
    the rectangles they divide the image into, not "squares": unequal
    counts (or a width/height ratio that doesn't match count_x/count_y)
    produce rectangular cells, not square ones.

    Args:
        width: Image width in pixels.
        height: Image height in pixels.
        count_x: Number of rectangles along the width. Must be >= 1.
        count_y: Number of rectangles along the height. Must be >= 1.

    Returns:
        A 2D uint8 array of shape (height, width) with values 0 or 255.

    Raises:
        ValueError: If count_x or count_y is less than 1.
    """
    if count_x < 1:
        raise ValueError(f"count_x {count_x} must be >= 1")
    if count_y < 1:
        raise ValueError(f"count_y {count_y} must be >= 1")

    rows = (np.arange(height) * count_y // height) % 2
    cols = (np.arange(width) * count_x // width) % 2
    pattern = np.logical_xor(rows[:, None], cols[None, :])
    return (pattern * 255).astype(np.uint8)


def astronaut(*, width: int = 512, height: int = 512) -> np.ndarray:
    """Load a bundled real-world grayscale reference image.

    Same parameters and pixel values as the `dictk astronaut` CLI
    command, minus the file write — see the `dictk` package docstring for
    why the API layer stops at the array.

    The source is a NASA portrait of astronaut Eileen Collins, from the
    NASA Great Images database ("No known copyright restrictions, released
    into the public domain."). It's bundled as a color image and converted
    with `rgba_to_gray`; unlike `rosta` and `checkerboard`, it isn't
    procedurally generated, so `width`/`height` other than the native
    512x512 resize the source image (via `scipy.ndimage.zoom`) rather than
    computing a fresh pattern at that size.

    Args:
        width: Image width in pixels. Must be >= 1.
        height: Image height in pixels. Must be >= 1.

    Returns:
        A 2D uint8 array of shape (height, width).

    Raises:
        ValueError: If width or height is less than 1.
    """
    if width < 1:
        raise ValueError(f"width {width} must be >= 1")
    if height < 1:
        raise ValueError(f"height {height} must be >= 1")

    asset_path = importlib.resources.files("dictk") / "data" / "astronaut.png"
    with importlib.resources.as_file(asset_path) as path:
        color = read(path=path)
    gray = rgba_to_gray(color)

    native_height, native_width = gray.shape
    if (width, height) == (native_width, native_height):
        return gray

    zoom_factors = (height / native_height, width / native_width)
    resized = zoom(gray.astype(np.float64), zoom_factors, order=3)
    return np.clip(resized, 0, 255).astype(np.uint8)


def is_rgba(arr: np.ndarray) -> bool:
    """Check whether an image array is in RGB or RGBA format.

    Args:
        arr: Input image array.

    Returns:
        True if the array is 3D with 3 or 4 channels, False otherwise.
    """
    return arr.ndim == 3 and arr.shape[2] in (3, 4)


def rgba_to_gray(arr: np.ndarray) -> np.ndarray:
    """Convert an RGB(A) image to grayscale by averaging the RGB channels.

    Args:
        arr: Input image array, either 2D (grayscale) or 3D (color).

    Returns:
        A 2D grayscale image array. If the input is already 2D, it is
        returned unchanged.

    Raises:
        ValueError: If the array is neither 2D nor a 3-or-4-channel 3D array.
    """
    if arr.ndim == 2:
        return arr

    if is_rgba(arr):
        return np.mean(arr[:, :, :3], axis=2).astype(arr.dtype)

    raise ValueError(
        "Input array must be either 2D (grayscale) or 3D with 3 or 4 channels (color)."
    )


def combine(*, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Combine two images by averaging their pixel values.

    Args:
        a: First image, 2D grayscale or 3D color.
        b: Second image, same shape as `a` once converted to grayscale.

    Returns:
        A 2D uint8 array, normalized to the range [0, 255].

    Raises:
        ValueError: If the grayscale-converted images don't share a shape.
    """
    gray_a = rgba_to_gray(a)
    gray_b = rgba_to_gray(b)

    if gray_a.shape != gray_b.shape:
        raise ValueError(
            f"shape mismatch: a.shape={gray_a.shape}, b.shape={gray_b.shape}"
        )

    combined = gray_a.astype(np.float64) + gray_b.astype(np.float64)
    return (combined / combined.max() * 255).astype(np.uint8)


def brightness(*, arr: np.ndarray, factor: float) -> np.ndarray:
    """Adjust image brightness by an additive shift, clipped to [0, 255].

    Brightness *translates* the pixel-intensity histogram: every pixel is
    shifted by the same amount, so dark areas lighten right along with
    bright ones (unlike a multiplicative scale, where a black pixel would
    stay exactly black). factor=1.0 leaves the image unchanged; factor=1.5
    shifts every pixel by +127.5*0.5 = +63.75, factor=2.0 by +127.5.

    Args:
        arr: A 2D grayscale image array.
        factor: Brightness factor. 1.0 is unchanged; > 1.0 brightens
            (shifts toward white); < 1.0 darkens (shifts toward black).

    Returns:
        A 2D uint8 array, same shape as `arr`.
    """
    max_pixel_value = 255.0
    offset = (factor - 1.0) * (max_pixel_value / 2.0)
    shifted = arr.astype(np.float64) + offset
    return np.clip(shifted, 0, max_pixel_value).astype(np.uint8)


def contrast(*, arr: np.ndarray, factor: float) -> np.ndarray:
    """Adjust image contrast by scaling around the mean, clipped to [0, 255].

    Contrast *stretches* the pixel-intensity histogram outward from its own
    mean, rather than shifting it: the mean stays roughly the same, while
    values spread further from it. factor=1.0 leaves the image unchanged;
    factor=0.0 collapses every pixel to the mean (a flat gray image);
    factor > 1.0 pushes values further toward 0 and 255.

    Args:
        arr: A 2D grayscale image array.
        factor: Contrast factor. 1.0 is unchanged; > 1.0 increases
            contrast; between 0.0 and 1.0 decreases it.

    Returns:
        A 2D uint8 array, same shape as `arr`.
    """
    mean = arr.astype(np.float64).mean()
    stretched = (arr.astype(np.float64) - mean) * factor + mean
    return np.clip(stretched, 0, 255).astype(np.uint8)


def _backward_map(
    arr: np.ndarray, xs_source: np.ndarray, ys_source: np.ndarray
) -> np.ndarray:
    """Sample `arr` via bilinear interpolation at (xs_source, ys_source).

    Shared by geometric-transform functions (`stretch`, `translate`, ...):
    each computes where every output pixel's source coordinate falls under
    its own inverse transform, then hands the resulting coordinate grids
    here to do the actual sampling. Coordinates outside `arr`'s bounds are
    filled with black (0).

    Args:
        arr: A 2D grayscale image array.
        xs_source: Source x-coordinate for each output pixel, shape (height, width).
        ys_source: Source y-coordinate for each output pixel, shape (height, width).

    Returns:
        A 2D uint8 array, same shape as `arr`.
    """
    height, width = arr.shape
    interpolator = RegularGridInterpolator(
        points=(np.arange(height), np.arange(width)),
        values=arr.astype(np.float64),
        method="linear",
        bounds_error=False,
        fill_value=0.0,
    )
    points = np.stack((ys_source.ravel(), xs_source.ravel()), axis=1)
    deformed = interpolator(points).reshape(arr.shape)
    return np.clip(deformed, 0, 255).astype(np.uint8)


def stretch(
    *, arr: np.ndarray, factor_x: float = 1.0, factor_y: float = 1.0
) -> np.ndarray:
    """Apply a uniaxial or biaxial stretch, pivoting on the image origin.

    Mimics a continuum-mechanics stretch deformation gradient
    diag(factor_x, factor_y), anchored at the image's top-left corner
    (x=0, y=0): that corner stays fixed, and content grows (factor > 1.0)
    or shrinks (factor < 1.0) away from it along each axis. Uses backward
    mapping — for each output pixel, the inverse of the stretch locates
    its source coordinate in `arr`, with bilinear interpolation for
    non-integer source coordinates — so the result has no gaps, unlike
    naively moving each source pixel forward. A factor < 1.0 shrinks
    content toward the origin, leaving black (fill value 0) margins along
    the far (bottom/right) edges.

    Args:
        arr: A 2D grayscale image array.
        factor_x: Stretch factor along the x-axis. Must be > 0.
        factor_y: Stretch factor along the y-axis. Must be > 0.

    Returns:
        A 2D uint8 array, same shape as `arr`.

    Raises:
        ValueError: If factor_x or factor_y is <= 0.
    """
    if factor_x <= 0:
        raise ValueError(f"factor_x {factor_x} must be > 0")
    if factor_y <= 0:
        raise ValueError(f"factor_y {factor_y} must be > 0")

    height, width = arr.shape
    xs, ys = np.meshgrid(np.arange(width), np.arange(height))

    # Backward mapping, pivoting on the origin (0, 0): for each output
    # pixel, the inverse of the stretch gives the coordinate to sample
    # from in the original image.
    xs_source = xs / factor_x
    ys_source = ys / factor_y

    return _backward_map(arr, xs_source, ys_source)


def translate(*, arr: np.ndarray, dx: float = 0.0, dy: float = 0.0) -> np.ndarray:
    """Apply a rigid-body translation: every pixel shifts by (dx, dy).

    A pure displacement, with no change in shape or size — the simplest
    transformation category. Uses the same backward-mapping approach as
    `stretch`, so non-integer displacements are handled with bilinear
    interpolation rather than rounding. Content shifted in from outside
    the original bounds is filled with black (fill value 0).

    Args:
        arr: A 2D grayscale image array.
        dx: Displacement in pixels along the x-axis; positive moves
            content right.
        dy: Displacement in pixels along the y-axis; positive moves
            content down.

    Returns:
        A 2D uint8 array, same shape as `arr`.
    """
    height, width = arr.shape
    xs, ys = np.meshgrid(np.arange(width), np.arange(height))

    # Backward mapping: the source of output pixel (x, y) is (x - dx, y - dy).
    xs_source = xs - dx
    ys_source = ys - dy

    return _backward_map(arr, xs_source, ys_source)


def rotate(*, arr: np.ndarray, angle: float) -> np.ndarray:
    """Apply a rigid-body rotation, pivoting on the image origin.

    Rotates content by `angle` degrees, positive counterclockwise,
    pivoting on the image's top-left corner (0, 0) rather than its
    center — consistent with `stretch` and `translate`'s pivot choice in
    this codebase, but unlike a typical "object spins in place" rotation
    example: most content swings away from that fixed corner, similar to
    a door on a hinge. Uses the same backward-mapping approach as
    `stretch` and `translate`, so non-integer source coordinates are
    bilinearly interpolated, and any pixel with no corresponding source
    coordinate within `arr`'s bounds is filled with black (fill value 0).

    Args:
        arr: A 2D grayscale image array.
        angle: Rotation angle in degrees; positive is counterclockwise.

    Returns:
        A 2D uint8 array, same shape as `arr`.
    """
    height, width = arr.shape
    xs, ys = np.meshgrid(np.arange(width), np.arange(height))

    theta = np.deg2rad(angle)
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)

    # Backward mapping: applying the inverse (-angle) rotation to each
    # output coordinate gives the coordinate to sample from.
    xs_source = cos_theta * xs + sin_theta * ys
    ys_source = -sin_theta * xs + cos_theta * ys

    return _backward_map(arr, xs_source, ys_source)


def shear(*, arr: np.ndarray, shear_x: float = 0.0, shear_y: float = 0.0) -> np.ndarray:
    """Apply a simple shear, pivoting on the image origin.

    Mimics a continuum-mechanics shear deformation gradient
    [[1, shear_x], [shear_y, 1]], anchored at the image's top-left corner
    (x=0, y=0), consistent with `stretch`, `translate`, and `rotate`'s
    pivot choice in this codebase: horizontal planes slide relative to
    each other by an amount proportional to their y-coordinate
    (shear_x), and/or vertical planes slide by an amount proportional to
    their x-coordinate (shear_y). Uses the same backward-mapping approach
    as the other transform functions, so non-integer source coordinates
    are bilinearly interpolated, and any pixel with no corresponding
    source coordinate within `arr`'s bounds is filled with black (fill
    value 0).

    Args:
        arr: A 2D grayscale image array.
        shear_x: Horizontal shear factor.
        shear_y: Vertical shear factor.

    Returns:
        A 2D uint8 array, same shape as `arr`.

    Raises:
        ValueError: If shear_x * shear_y == 1, which makes the
            deformation gradient singular (non-invertible).
    """
    determinant = 1.0 - shear_x * shear_y
    if determinant == 0:
        raise ValueError(
            f"shear_x {shear_x} and shear_y {shear_y} produce a singular "
            "deformation gradient (shear_x * shear_y == 1)"
        )

    height, width = arr.shape
    xs, ys = np.meshgrid(np.arange(width), np.arange(height))

    # Backward mapping: invert the shear deformation gradient
    # [[1, shear_x], [shear_y, 1]] to find each output pixel's source.
    xs_source = (xs - shear_x * ys) / determinant
    ys_source = (-shear_y * xs + ys) / determinant

    return _backward_map(arr, xs_source, ys_source)


def complex_deform(
    *,
    arr: np.ndarray,
    factor_x: float = 1.0,
    factor_y: float = 1.0,
    angle: float = 0.0,
) -> np.ndarray:
    """Apply an anisotropic stretch composed with a rotation, in one pass.

    Composes a stretch (deformation gradient diag(factor_x, factor_y))
    with a rotation (`angle` degrees, counterclockwise): the combined
    deformation gradient is F = R(angle) @ diag(factor_x, factor_y), i.e.
    the stretch is applied first and the rotation second. Applying both
    in a single backward-mapping pass (rather than calling `stretch` and
    then `rotate` separately) avoids the extra blur of interpolating
    twice. Represents realistic loading scenarios where materials
    experience multiple simultaneous deformation modes — typically the
    hardest case for correlation algorithms. Pivots on the image's
    top-left corner (0, 0), consistent with `stretch`, `translate`,
    `rotate`, and `shear`'s pivot choice in this codebase.

    Args:
        arr: A 2D grayscale image array.
        factor_x: Stretch factor along the x-axis, applied before the
            rotation. Must be > 0.
        factor_y: Stretch factor along the y-axis, applied before the
            rotation. Must be > 0.
        angle: Rotation angle in degrees, applied after the stretch;
            positive is counterclockwise.

    Returns:
        A 2D uint8 array, same shape as `arr`.

    Raises:
        ValueError: If factor_x or factor_y is <= 0.
    """
    if factor_x <= 0:
        raise ValueError(f"factor_x {factor_x} must be > 0")
    if factor_y <= 0:
        raise ValueError(f"factor_y {factor_y} must be > 0")

    height, width = arr.shape
    xs, ys = np.meshgrid(np.arange(width), np.arange(height))

    theta = np.deg2rad(angle)
    cos_theta = np.cos(theta)
    sin_theta = np.sin(theta)

    # Backward mapping for F = R(angle) @ diag(factor_x, factor_y):
    # F_inv = diag(1/factor_x, 1/factor_y) @ R(-angle), applied to each
    # output coordinate to find its source. Un-rotate first, then unscale.
    xs_rotated = cos_theta * xs + sin_theta * ys
    ys_rotated = -sin_theta * xs + cos_theta * ys
    xs_source = xs_rotated / factor_x
    ys_source = ys_rotated / factor_y

    return _backward_map(arr, xs_source, ys_source)


def crack_dislocation(*, arr: np.ndarray, offset: float = 8.0) -> np.ndarray:
    """Apply a discontinuous vertical-crack displacement field.

    Splits the image with a vertical crack at x = width / 2: the left
    half shifts down by `offset` pixels and the right half shifts up by
    `offset` pixels, producing a displacement field that jumps
    discontinuously across the crack line — unlike every other transform
    in this module, which varies smoothly. Standard DIC assumes smooth
    displacements and cannot capture this jump; cases like this motivate
    the Heaviside finite-element formulation. Uses the same backward
    mapping as the other transform functions, just with a piecewise
    (rather than single-matrix) displacement field, so non-integer
    source coordinates are bilinearly interpolated, and any pixel with
    no corresponding source coordinate within `arr`'s bounds is filled
    with black (fill value 0).

    Args:
        arr: A 2D grayscale image array.
        offset: Displacement in pixels; the left half (x < width / 2)
            shifts down by this amount, the right half shifts up by it.

    Returns:
        A 2D uint8 array, same shape as `arr`.
    """
    height, width = arr.shape
    xs, ys = np.meshgrid(np.arange(width), np.arange(height))

    xs_source = xs.astype(np.float64)
    ys_source = ys.astype(np.float64)

    left_half = xs < (width / 2)
    ys_source[left_half] -= offset
    ys_source[~left_half] += offset

    return _backward_map(arr, xs_source, ys_source)


def read(*, path: Path) -> np.ndarray:
    """Read an image file into a NumPy array.

    Args:
        path: Path to the image file.

    Returns:
        The image as a NumPy array.
    """
    return iio.imread(path)


def write_svg(*, arr: np.ndarray, path: Path) -> None:
    """Write a NumPy array to an SVG file.

    SVG is a vector format with no native pixel-grid concept, so the array
    is PNG-encoded and embedded as a base64 data URI inside a minimal SVG
    wrapper (the standard way to carry raster data in SVG) rather than
    traced into vector shapes.

    Args:
        arr: The image array to save.
        path: The output file path.
    """
    height, width = arr.shape[:2]
    png_bytes = iio.imwrite("<bytes>", arr, extension=".png")
    encoded = base64.b64encode(png_bytes).decode("ascii")

    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        f'  <image width="{width}" height="{height}" '
        f'xlink:href="data:image/png;base64,{encoded}"/>\n'
        "</svg>\n"
    )
    Path(path).write_text(svg, encoding="ascii")


def write(*, arr: np.ndarray, path: Path) -> None:
    """Write a NumPy array to an image file.

    Dispatches on the file extension: `.svg` is handled by `write_svg`
    (embedding a raster PNG in an SVG wrapper); every other extension
    (`.tiff`, `.png`, `.jpg`, ...) is handled by imageio directly.

    Args:
        arr: The image array to save.
        path: The output file path.
    """
    if Path(path).suffix.lower() == ".svg":
        write_svg(arr=arr, path=path)
        return

    iio.imwrite(path, arr)


def describe(arr: np.ndarray) -> str:
    """Format a description of an image array's type, shape, and color format.

    Args:
        arr: The image array to describe.

    Returns:
        A multi-line description string.
    """
    lines = [
        f"Type: {type(arr)}",
        f"Shape: {arr.shape}",
        f"Dtype: {arr.dtype}",
    ]

    match arr.shape:
        case (_height, _width):
            lines.append("The image is grayscale.")
        case (_height, _width, 3):
            lines.append("The image is color (RGB).")
        case (_height, _width, 4):
            lines.append("The image is color (RGBA, includes alpha channel).")
        case _:
            lines.append("The image has an unsupported format.")

    return "\n".join(lines)


def histogram_save(*, arr: np.ndarray, path: Path, dpi: int = 300) -> None:
    """Save a histogram of pixel intensities [0, 255] for a grayscale image.

    Args:
        arr: The 2D grayscale image array, expected type uint8, range [0, 255].
        path: The output file path for the histogram image; format is
            inferred from the extension by matplotlib's savefig (e.g.
            .png), not dictk's own write/write_svg.
        dpi: Resolution of the saved figure.
    """
    plt.figure()
    plt.hist(arr.ravel(), bins=256, range=(0, 255), color="black", alpha=0.7)
    plt.title(f"pixel histogram intensity\n{path}", fontsize=8)
    plt.xlabel("pixel intensity (0-255)")
    plt.ylabel("frequency")
    plt.savefig(path, dpi=dpi)
    plt.close()
