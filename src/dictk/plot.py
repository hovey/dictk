"""Matplotlib-based figure generation for dictk's image and DIC data."""

from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

import numpy as np
from matplotlib import patches
from matplotlib import patheffects
from matplotlib import pyplot as plt
from matplotlib.colors import Colormap
from matplotlib.path import Path as MarkerPath

from dictk.correlation import WindowingMethod, _kernel_pad, phase_correlation, window
from dictk.image import PixelCoordinate, SubpixelCoordinate, subimage


# Shared figure scale (pixels of image data per inch) for
# subimage_bounds_plot() and subimage_plot(), so each saved figure's size
# is proportional to its actual pixel content rather than a fixed default
# figure size -- letting the two be visually compared for relative size
# instead of both rendering at roughly the same size regardless of how
# many pixels each actually covers.
_FIGURE_PIXELS_PER_INCH = 100

# The first 12 colors of matplotlib's "tab20" (Tableau 20) colormap: 6 hues
# (blue, orange, green, red, purple, brown), each as a dark/light pair.
# Deliberately stops short of tab20's gray pair (its indices 14-15) --
# gray has no hue to contrast against a grayscale image with, so it all
# but disappears drawn on top of one.
_TABLEAU_PALETTE = (
    "#1f77b4",
    "#aec7e8",  # blue
    "#ff7f0e",
    "#ffbb78",  # orange
    "#2ca02c",
    "#98df8a",  # green
    "#d62728",
    "#ff9896",  # red
    "#9467bd",
    "#c5b0d5",  # purple
    "#8c564b",
    "#c49c94",  # brown
)


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
    figsize: tuple[float, float] | None = None,
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
        figsize: Optional (width, height) in inches for the saved figure
            (both panels combined). By default the canvas is sized from
            `image`/the subimage's own data extent (so a small subimage
            yields a small figure); pass this to override with a fixed
            size instead -- e.g. matplotlib's own default, `(6.4, 4.8)`,
            where its default font sizes and line widths look as intended.
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
    # Small up-right offset for marker labels, so label text doesn't sit
    # directly on top of its own marker.
    label_offset = max(image_width, image_height) * 0.03
    label_font_size = 12
    # source_origin_label/origin_label sit just up-right of a marker at
    # (0, 0) -- the top-left corner of the panel's own content -- so only
    # the top margin (where a label there would land, above the panel
    # title) needs widening to fit one; left/right/bottom stay at the
    # default margin instead of also carrying that extra, unused space.
    # Anchored so the label's own bottom edge sits `label_offset` above
    # the marker (matching the gap already below the marker, down to the
    # box edge at y=0) and its top edge sits that same `label_offset`
    # below the panel's own top border -- the same gap on both sides of
    # the label, rather than a fixed multiple of the font size that
    # doesn't relate to the marker's own gap below.
    top_margin = margin
    if source_origin_label is not None or origin_label is not None:
        label_text_height = label_font_size / 72 * _FIGURE_PIXELS_PER_INCH
        top_margin = max(margin, 2 * label_offset + label_text_height)
    x_min = min(0, origin.x) - margin
    x_max = max(image_width, origin.x + width) + margin
    y_min = min(0, origin.y) - top_margin
    y_max = max(image_height, origin.y + height) + margin

    # A thin white outline keeps every marker label legible against
    # whatever's directly behind it in the image content.
    label_outline = [patheffects.withStroke(linewidth=1, foreground="white")]

    if figsize is None:
        panel_width = (x_max - x_min) / _FIGURE_PIXELS_PER_INCH
        panel_height = (y_max - y_min) / _FIGURE_PIXELS_PER_INCH
        figsize = (panel_width * 2, panel_height)
    fig, (ax_left, ax_right) = plt.subplots(
        1, 2, figsize=figsize, constrained_layout=True
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
            fontsize=label_font_size,
            va="bottom",
            path_effects=label_outline,
        )
    if origin_label is not None:
        ax_left.text(
            origin.x + label_offset,
            origin.y - label_offset,
            origin_label,
            color=color,
            fontsize=label_font_size,
            va="bottom",
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
            point.x - origin.x,
            point.y - origin.y,
            marker="o",
            color=point_color,
            markersize=6,
        )
    if origin_label is not None:
        ax_right.text(
            label_offset,
            -label_offset,
            origin_label,
            color=color,
            fontsize=label_font_size,
            va="bottom",
            path_effects=label_outline,
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
    figsize: tuple[float, float] | None = None,
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
        figsize: Optional (width, height) in inches for the saved figure.
            By default the canvas is sized from the annotations' own
            data extent (so a small image yields a small figure); pass
            this to override with a fixed size instead -- e.g.
            matplotlib's own default, `(6.4, 4.8)`, where its default
            font sizes and line widths look as intended.
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
    # Small up-right offset for point labels, so label text doesn't sit
    # directly on top of its own marker.
    label_offset = max(image_width, image_height) * 0.03
    label_font_size = 12
    # Point labels sit just up-right of their marker, so only the top
    # margin (where a label on a point near y=0 would land, above the
    # title) needs widening to fit one; left/right/bottom stay at the
    # default margin instead of also carrying that extra, unused space.
    # Anchored so the label's own bottom edge sits `label_offset` above
    # its marker (matching the gap already below the marker, e.g. down
    # to a box edge at y=0) and its top edge sits that same
    # `label_offset` below the figure's own top border -- the same gap
    # on both sides of the label, rather than a fixed multiple of the
    # font size that doesn't relate to the marker's own gap below.
    top_margin = margin
    if points:
        label_text_height = label_font_size / 72 * _FIGURE_PIXELS_PER_INCH
        top_margin = max(margin, 2 * label_offset + label_text_height)
    x_min = min(0, *endpoints_x) - margin
    x_max = max(image_width, *endpoints_x) + margin
    y_min = min(0, *endpoints_y) - top_margin
    y_max = max(image_height, *endpoints_y) + margin
    label_outline = [patheffects.withStroke(linewidth=1, foreground="white")]

    if figsize is None:
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
            fontsize=label_font_size,
            va="bottom",
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
        (
            (axis_length, 0),
            (axis_length, -label_offset),
            "red",
            "x",
            "center",
            "bottom",
        ),
        (
            (0, axis_length),
            (-label_offset, axis_length),
            "green",
            "y",
            "right",
            "center",
        ),
    ):
        ax_right.annotate(
            "",
            xy=axis_head,
            xytext=(0, 0),
            arrowprops={"color": color, "width": 1.5, "headwidth": 8, "shrink": 0},
        )
        ax_right.text(
            *label_pos, label, color=color, fontsize=label_font_size, ha=ha, va=va
        )

    ax_right.set_title("reference frame")

    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


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


def _correlation_surface_ticks(size: int) -> list[int]:
    """Fixed Correlation Surface tick marks for an axis of length `size`.

    Correlation Visualization shows this panel seven times: CC/NCC/ZCC/
    ZNCC's 51x51 "valid" surfaces, and phase correlation's three
    same-shape-as-`search` 100x100 ones (no windowing/Hann/Hamming).
    Rather than matplotlib's own per-panel default (which lands on
    different steps for the two sizes, and doesn't always reach the
    axis's own upper bound), each of those two known sizes gets one
    fixed, round-number tick list spanning its own full extent -- so
    every 51x51 panel matches every other 51x51 panel, and every 100x100
    one matches every other 100x100 one, when read side by side.

    Any other `size` (e.g. Recoverable Displacement Range's 300x300
    quadrant figures, `search_margin=150` against `astronaut0`'s own
    300px canvas) falls back to a generated five-interval, round-number
    step instead of matplotlib's own default -- the original problem
    this function exists to fix in the first place. Without this
    fallback, every `size` other than the two known ones used to
    silently reuse the 100-wide list regardless of its own actual
    extent, cramming every tick into the axis's first 100 pixels.

    Args:
        size: The axis's length in pixels (a Correlation Surface panel's
            own height or width).

    Returns:
        `[0, 10, 20, 30, 40, 50]` for the 51-wide "valid" surfaces,
        `[0, 20, 40, 60, 80, 100]` for the 100-wide full-search ones,
        otherwise five evenly-spaced ticks from 0 up to (as close as a
        multiple-of-10 step allows) `size` itself.
    """
    if size == 51:
        return [0, 10, 20, 30, 40, 50]
    if size == 100:
        return [0, 20, 40, 60, 80, 100]
    step = max(10, round(size / 5 / 10) * 10)
    return list(range(0, size + 1, step))


def _correlation_quadrant_plot(
    *,
    kernel: np.ndarray,
    search: np.ndarray,
    correlation_surface: np.ndarray,
    title: str,
    path: Path,
    figsize: tuple[float, float] = (8.0, 8.0),
    dpi: int = 300,
    vicinity_margin: int = 4,
    reported_position: PixelCoordinate | None = None,
    reported_position_label: str = "reported",
    centered: bool = False,
) -> None:
    """Shared renderer behind spatial_correlation_quadrant_plot() and
    phase_correlation_quadrant_plot() -- private (never published by
    pdoc), so those two public functions each carry their own complete
    docstring rather than pointing here.

    Draws the Fixed Image / Moving Image / correlation surface / Solution
    Vicinity 2x2 layout for whatever `correlation_surface` array it's
    given. Shape-agnostic on purpose: works identically whether the
    surface came from a spatial-domain "valid" computation (smaller than
    `search`) or a same-shape-as-`search` Fourier-domain one -- it only
    ever takes that array's own argmax and plots whatever shape comes in.

    `reported_position`, if given, is a second position in `search`'s own
    local frame (same top-left-corner convention as the surface's own
    peak) -- some other, external computation's *claimed* answer, which
    may differ from where `correlation_surface` itself actually peaks.
    Drawn as a second, dotted magenta box on the Fixed Image panel,
    distinct from the surface's own yellow dashed one, with a legend
    naming both. `None` (default) omits it entirely, leaving every
    existing figure byte-identical to before this parameter existed.

    `centered`, if `True`, pads the Moving Image panel's `kernel` display
    the same way `dictk.translation.locate` does internally (via
    `_kernel_pad(..., centered=True)`) instead of the permanent
    bottom-right-only padding `phase_correlation` itself always uses (see
    [Recoverable Displacement
    Range](../../getting_started/recoverable_displacement_range.html) for
    why those two conventions differ). `correlation_surface`'s own raw
    `argmax` is always relative to *that* padding, so with centered
    padding the Fixed Image panel's box needs `kernel_padded`'s own
    content offset added back in to land on the true match position --
    `correlation_surface`'s peak itself (and the Correlation Surface/
    Solution Vicinity panels showing it) is unaffected, still the raw
    array position. Default `False` reproduces the original bottom-right
    padding exactly, byte-identical to every figure from before this
    parameter existed.
    """
    if search.shape[0] < kernel.shape[0] or search.shape[1] < kernel.shape[1]:
        raise ValueError(
            f"search shape {search.shape} must be >= kernel shape {kernel.shape} "
            "in both dimensions"
        )

    search_height, search_width = search.shape
    kernel_height, kernel_width = kernel.shape

    peak_y, peak_x = np.unravel_index(
        np.argmax(correlation_surface), correlation_surface.shape
    )
    peak_y, peak_x = int(peak_y), int(peak_x)

    if centered:
        # Same padding dictk.translation.locate() applies internally --
        # kernel_padded's own content no longer starts at (0, 0), so the
        # Fixed Image panel's box needs that offset added back in to the
        # surface's own raw peak to land on the true match position.
        kernel_padded, pad_before_height, pad_before_width = _kernel_pad(
            kernel=kernel, shape=search.shape, centered=True
        )
        box_x = (peak_x + pad_before_width) % search_width
        box_y = (peak_y + pad_before_height) % search_height
    else:
        # Same bottom/right zero-padding dictk.translation.locate() applied
        # before its own fix, here purely for display so the kernel's
        # content sits at the correct corner of a search-shaped canvas.
        kernel_padded = np.pad(
            kernel,
            ((0, search_height - kernel_height), (0, search_width - kernel_width)),
        )
        box_x, box_y = peak_x, peak_y

    with plt.rc_context({"font.family": "serif", "mathtext.fontset": "cm"}):
        fig, axes = plt.subplots(2, 2, figsize=figsize, constrained_layout=True)
        fig.suptitle(title)
        ax1, ax2, ax3, ax4 = axes.flat

        im1 = ax1.imshow(
            search,
            cmap="gray",
            vmin=0,
            vmax=255,
            origin="upper",
            extent=(0, search_width, search_height, 0),
        )
        plt.colorbar(im1, ax=ax1, shrink=0.8)
        ax1.add_patch(
            patches.Rectangle(
                (box_x, box_y),
                kernel_width,
                kernel_height,
                edgecolor="yellow",
                facecolor="none",
                linestyle="--",
                linewidth=1,
                alpha=0.8,
                label="correlation surface peak",
            )
        )
        ax1.axvline(x=box_x, color="red", linestyle="--", linewidth=1, alpha=0.8)
        ax1.axhline(y=box_y, color="green", linestyle="--", linewidth=1, alpha=0.8)
        xticks = {0, search_width, box_x}
        yticks = {0, search_height, box_y}
        if reported_position is not None:
            ax1.add_patch(
                patches.Rectangle(
                    (reported_position.x, reported_position.y),
                    kernel_width,
                    kernel_height,
                    edgecolor="magenta",
                    facecolor="none",
                    linestyle=":",
                    linewidth=1.5,
                    alpha=0.5,
                    label=reported_position_label,
                )
            )
            xticks.add(reported_position.x)
            yticks.add(reported_position.y)
            ax1.legend(loc="upper right", fontsize=7, framealpha=0.9)
        ax1.set_xticks(sorted(xticks))
        ax1.set_yticks(sorted(yticks))
        for label in ax1.get_xticklabels():
            if label.get_text() == str(box_x):
                label.set_color("red")
        for label in ax1.get_yticklabels():
            if label.get_text() == str(box_y):
                label.set_color("green")
        ax1.set_title(r"Fixed Image with frame $\mathcal{S}$")
        ax1.set_xlabel("x (pixels)")
        ax1.set_ylabel("y (pixels)")

        im2 = ax2.imshow(
            kernel_padded,
            cmap="gray",
            vmin=0,
            vmax=255,
            origin="upper",
            extent=(0, search_width, search_height, 0),
        )
        plt.colorbar(im2, ax=ax2, shrink=0.8)
        if centered:
            kernel_xticks = {
                0,
                search_width,
                pad_before_width,
                pad_before_width + kernel_width,
            }
            kernel_yticks = {
                0,
                search_height,
                pad_before_height,
                pad_before_height + kernel_height,
            }
            ax2.set_title(r"Moving Image with frame $\mathcal{K}$ (centered)")
        else:
            kernel_xticks = {0, search_width, kernel_width}
            kernel_yticks = {0, search_height, kernel_height}
            ax2.set_title(r"Moving Image with frame $\mathcal{K}$")
        ax2.set_xticks(sorted(kernel_xticks))
        ax2.set_yticks(sorted(kernel_yticks))
        ax2.set_xlabel("x (pixels)")
        ax2.set_ylabel("y (pixels)")

        im3 = ax3.imshow(correlation_surface, cmap="viridis", origin="upper")
        plt.colorbar(im3, ax=ax3, shrink=0.8)
        ax3.add_patch(
            patches.Circle(
                (peak_x, peak_y),
                radius=vicinity_margin,
                edgecolor="red",
                facecolor="none",
                linewidth=1.5,
            )
        )
        ax3.set_title("Correlation Surface")
        ax3.set_xlabel(r"$\Delta x$ offset (pixels)")
        ax3.set_ylabel(r"$\Delta y$ offset (pixels)")
        # Fixed ticks, not matplotlib's own auto-choice -- see
        # _correlation_surface_ticks() for why.
        surface_height, surface_width = correlation_surface.shape
        ax3.set_xticks(_correlation_surface_ticks(surface_width))
        ax3.set_yticks(_correlation_surface_ticks(surface_height))

        im4 = ax4.imshow(correlation_surface, cmap="viridis", origin="upper")
        plt.colorbar(im4, ax=ax4, shrink=0.8)
        ax4.set_xlim(peak_x - vicinity_margin, peak_x + vicinity_margin)
        ax4.set_ylim(peak_y + vicinity_margin, peak_y - vicinity_margin)
        # Same circle as ax3, same radius, in the same data coordinates --
        # since this panel is zoomed to exactly peak +/- vicinity_margin,
        # the circle exactly reaches this panel's own edges, appearing
        # clipped by them rather than fully visible as it was in ax3.
        ax4.add_patch(
            patches.Circle(
                (peak_x, peak_y),
                radius=vicinity_margin,
                edgecolor="red",
                facecolor="none",
                linewidth=1.5,
            )
        )
        ax4.set_title("Solution Vicinity")
        ax4.set_xlabel(r"$\Delta x$ offset (pixels)")
        ax4.set_ylabel(r"$\Delta y$ offset (pixels)")

        fig.savefig(path, dpi=dpi)
        plt.close(fig)


def spatial_correlation_quadrant_plot(
    *,
    kernel: np.ndarray,
    search: np.ndarray,
    correlation_surface: np.ndarray,
    title: str,
    path: Path,
    figsize: tuple[float, float] = (8.0, 8.0),
    dpi: int = 300,
    vicinity_margin: int = 4,
) -> None:
    r"""Save a 2x2 composite figure illustrating one spatial-domain correlation criterion end to end.

    Reproduces a reference composite-figure layout used in prior DIC
    tooling -- Fixed Image, Moving Image, the correlation surface, and a
    zoomed Solution Vicinity -- using dictk's own spatial-domain
    correlation surfaces ([`dictk.correlation`](../correlation.html)'s
    `cc`/`ncc`/`zcc`/`zncc`) rather than a zero-padded whole-image FFT
    approach. See
    [`phase_correlation_quadrant_plot`](#phase_correlation_quadrant_plot)
    for the Fourier-domain sibling of this function.
    `correlation_surface`'s own argmax directly gives the kernel's found
    offset within `search`'s own frame $\mathcal{S}$ -- the same
    $\boldsymbol{r}_{SK/\mathcal{S}}$ quantity [Cross Correlation
    (CC)](../../getting_started/cross_correlation.html) walks through by
    hand -- so no separate found-position argument is needed the way that
    prior tooling's own composite-figure function takes one.

    Top-left panel: `search`, in its own local frame $\mathcal{S}$, with a
    yellow dashed box marking where `kernel` was found, plus red/green
    dashed guide lines through that box's origin (and matching red/green
    tick labels at that position). Top-right panel: `kernel` zero-padded
    (bottom and right) up to `search`'s own shape -- the same padding
    [`dictk.translation.locate`](../translation.html#locate) does
    internally -- so its content occupies only the top-left corner of an
    otherwise-black canvas the size of `search`, labeled frame
    $\mathcal{K}$. Bottom-left: `correlation_surface` as a heatmap, peak
    marked with a red circle of radius `vicinity_margin`. Bottom-right:
    the same surface, zoomed to exactly that same `vicinity_margin`
    pixels around its own peak -- the same circle reappears there too,
    now clipped by the panel's own edges, since the zoom window is
    exactly the circle's own bounding box.

    Text renders via matplotlib's built-in mathtext with a Computer-Modern
    -style serif font (`mathtext.fontset="cm"`), not real LaTeX
    (`text.usetex`) -- visually close to a real-LaTeX-rendered figure
    without a system TeX install, scoped to this function alone via
    `rc_context` so it can't leak into any other figure.

    Args:
        kernel: The extracted kernel subimage (2D grayscale array).
        search: The extracted search-area subimage (2D grayscale array);
            must be at least as large as `kernel` in both dimensions.
        correlation_surface: One of `dictk.correlation`'s `cc`/`ncc`/`zcc`/
            `zncc` surfaces, computed from this same `kernel`/`search`
            pair. Its own argmax is taken as the found position.
        title: Figure-level title naming the correlation criterion shown,
            e.g. `"Zero-mean Normalized Cross-Correlation (ZNCC)"` --
            rendered as a `suptitle` spanning the full figure width rather
            than the correlation-surface panel's own title, since panel
            titles are too narrow to reliably fit the longer criterion
            names without truncating or overlapping their colorbar.
        path: Output file path for the figure; format is inferred from the
            extension by matplotlib's savefig (e.g. .png).
        figsize: (width, height) in inches for the saved figure.
        dpi: Resolution of the saved figure.
        vicinity_margin: Half-width/height, in pixels, of the Solution
            Vicinity zoom window around the correlation surface's peak.

    Raises:
        ValueError: If `search` is smaller than `kernel` in either
            dimension.
    """
    _correlation_quadrant_plot(
        kernel=kernel,
        search=search,
        correlation_surface=correlation_surface,
        title=title,
        path=path,
        figsize=figsize,
        dpi=dpi,
        vicinity_margin=vicinity_margin,
    )


def phase_correlation_quadrant_plot(
    *,
    kernel: np.ndarray,
    search: np.ndarray,
    windowing: WindowingMethod | None = None,
    title: str = "Phase Correlation",
    path: Path,
    figsize: tuple[float, float] = (8.0, 8.0),
    dpi: int = 300,
    vicinity_margin: int = 4,
    reported_position: PixelCoordinate | None = None,
    reported_position_label: str = "reported",
    centered: bool = False,
) -> None:
    r"""Save a 2x2 composite figure illustrating Fourier-domain phase correlation end to end.

    The Fourier-domain sibling of
    [`spatial_correlation_quadrant_plot`](#spatial_correlation_quadrant_plot),
    sharing that function's exact panel layout (Fixed Image, Moving Image,
    correlation surface, zoomed Solution Vicinity). Unlike its sibling,
    this function takes raw `kernel`/`search` rather than a pre-computed
    surface: spatial-domain correlation has four interchangeable criteria
    (`cc`/`ncc`/`zcc`/`zncc`) a caller must choose between and compute
    themselves, but there is only one Fourier-domain flavor here, so this
    computes it internally via
    [`dictk.correlation.phase_correlation`](../correlation.html#phase_correlation)
    -- see that function's own docstring for the algorithm itself and why
    it lands in the same "robust to both brightness and contrast" tier as
    `zncc`, by a completely different mechanism.

    Top-left panel: `search`, in its own local frame $\mathcal{S}$, with a
    yellow dashed box marking where `kernel` was found, plus red/green
    dashed guide lines through that box's origin (and matching red/green
    tick labels at that position). Top-right panel: `kernel` zero-padded
    (bottom and right) up to `search`'s own shape -- the same padding
    [`dictk.translation.locate`](../translation.html#locate) does
    internally -- so its content occupies only the top-left corner of an
    otherwise-black canvas the size of `search`, labeled frame
    $\mathcal{K}$. Bottom-left: the phase correlation surface as a
    heatmap, peak marked with a red circle of radius `vicinity_margin`.
    Bottom-right: the same surface, zoomed to exactly that same
    `vicinity_margin` pixels around its own peak -- the same circle
    reappears there too, now clipped by the panel's own edges, since the
    zoom window is exactly the circle's own bounding box.

    Text renders via matplotlib's built-in mathtext with a Computer-Modern
    -style serif font (`mathtext.fontset="cm"`), not real LaTeX
    (`text.usetex`) -- visually close to a real-LaTeX-rendered figure
    without a system TeX install, scoped to this function alone via
    `rc_context` so it can't leak into any other figure.

    Args:
        kernel: The extracted kernel subimage (2D grayscale array).
        search: The extracted search-area subimage (2D grayscale array);
            must be at least as large as `kernel` in both dimensions.
        windowing: If given, passed straight through to
            [`phase_correlation`](../correlation.html#phase_correlation) --
            tapers `kernel`/`search` before computing the surface. The
            same tapered `kernel`/`search` are what the Fixed Image and
            Moving Image panels display too (windowed, *then* zero-padded
            for the Moving Image panel, same order the surface itself is
            computed in), so those panels always show what was actually
            correlated -- not a stale, untapered view next to a surface
            that no longer matches it. Default `None` applies no
            windowing, and the panels look exactly as they always have.
        title: Figure-level title, rendered as a `suptitle` spanning the
            full figure width. Defaults to `"Phase Correlation"` since
            there's only one flavor here -- override if different phrasing
            is wanted.
        path: Output file path for the figure; format is inferred from the
            extension by matplotlib's savefig (e.g. .png).
        figsize: (width, height) in inches for the saved figure.
        dpi: Resolution of the saved figure.
        vicinity_margin: Half-width/height, in pixels, of the Solution
            Vicinity zoom window around the correlation surface's peak.
        reported_position: A second position, in `search`'s own local
            frame (same top-left-corner convention as the surface's own
            peak), to mark on the Fixed Image panel as a dotted magenta
            box distinct from the surface's own yellow dashed one --
            some other, external computation's *claimed* answer, useful
            when that answer might disagree with where this surface
            itself actually peaks (e.g. [Recoverable Displacement
            Range](../../getting_started/recoverable_displacement_range.html)'s
            pre-fix `locate` reporting a wrapped, wrong position even
            though the underlying surface it was computed from peaks at
            the correct one). Default `None` omits it entirely, leaving
            every figure that doesn't pass it byte-identical to before
            this parameter existed.
        reported_position_label: Legend label for `reported_position`'s
            box, shown alongside "correlation surface peak" for the
            existing yellow one. Only rendered (and only then does a
            legend appear at all) when `reported_position` is given.
        centered: Passed straight through to
            [`phase_correlation`](../correlation.html#phase_correlation)'s
            own `centered` parameter -- the same convention
            `dictk.translation.locate` uses internally. The Moving Image
            panel's padding, and the Fixed Image panel's box position,
            follow suit (see `_correlation_quadrant_plot`'s own note on
            why the box needs the padding offset added back in). Default
            `False` matches `phase_correlation`'s own default exactly,
            byte-identical to every figure from before this parameter
            existed.

    Raises:
        ValueError: If `search` is smaller than `kernel` in either
            dimension.
    """
    correlation_surface = phase_correlation(
        kernel=kernel, search=search, windowing=windowing, centered=centered
    )
    display_kernel, display_search = kernel, search
    if windowing is not None:
        display_kernel = window(arr=kernel, method=windowing)
        display_search = window(arr=search, method=windowing)

    _correlation_quadrant_plot(
        kernel=display_kernel,
        search=display_search,
        correlation_surface=correlation_surface,
        title=title,
        path=path,
        figsize=figsize,
        dpi=dpi,
        vicinity_margin=vicinity_margin,
        reported_position=reported_position,
        reported_position_label=reported_position_label,
        centered=centered,
    )


def point_grid_boxes_plot(
    *,
    image: np.ndarray,
    points: Sequence[PixelCoordinate],
    margin_width: int,
    margin_height: int,
    label_prefix: str,
    figsize: tuple[float, float] | None = None,
    path: Path,
    dpi: int = 300,
) -> None:
    """Save a figure overlaying one uniquely colored, labeled box per point on `image`.

    For each of `points`, draws an unfilled rectangle centered on it, sized
    `2 * margin_width` by `2 * margin_height` -- e.g. a kernel (the patch
    [`dictk.translation.locate`](../translation.html#locate) would extract
    from the reference image) or a search area (its default search
    region), one call per box type. Agnostic to which: call it once with a
    kernel's margins and once with a search area's margins (on separate
    figures, or via multiple calls onto the same `ax` for a combined one)
    to compare either against point spacing at a glance -- e.g. whether
    neighboring kernels overlap, or whether search areas run off the image
    -- across the whole grid at once, not just one point.

    Each point's box gets its own color, cycling through a 12-color
    Tableau palette (`dictk.image._TABLEAU_PALETTE`; if there are more
    than 12 points, colors repeat), and its own legend entry -- `points[0]`
    labeled `"{label_prefix} 00"`, `points[19]` labeled `"{label_prefix}
    19"`, for a 20-point collection -- so overlapping boxes stay visually
    distinguishable and individually identifiable, not just grouped by box
    type.

    Args:
        image: Source 2D grayscale image array.
        points: The points to draw boxes around, in the image's own pixel
            reference frame. May be empty (an unmarked copy of `image` is
            saved).
        margin_width: Half each box's width, in pixels.
        margin_height: Half each box's height, in pixels.
        label_prefix: Legend label prefix for the boxes, e.g. `"kernel"`
            or `"search area"` -- each point's own zero-padded index is
            appended to it.
        figsize: Optional (width, height) in inches for the saved figure.
            By default the canvas is sized from `image`/the boxes' own
            data extent; pass this to override with a fixed size instead.
        path: Output file path for the figure; format is inferred from the
            extension by matplotlib's savefig (e.g. .png), not dictk's own
            write/write_svg.
        dpi: Resolution of the saved figure.
    """
    image_height, image_width = image.shape

    endpoints_x = [
        point.x + sign * margin_width for point in points for sign in (-1, 1)
    ]
    endpoints_y = [
        point.y + sign * margin_height for point in points for sign in (-1, 1)
    ]
    margin = max(image_width, image_height) * 0.05
    x_min = min(0, *endpoints_x, 0) - margin
    x_max = max(image_width, *endpoints_x, image_width) + margin
    y_min = min(0, *endpoints_y, 0) - margin
    y_max = max(image_height, *endpoints_y, image_height) + margin

    if figsize is None:
        figsize = (
            (x_max - x_min) / _FIGURE_PIXELS_PER_INCH,
            (y_max - y_min) / _FIGURE_PIXELS_PER_INCH,
        )
    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(
        image, cmap="gray", origin="upper", extent=(0, image_width, image_height, 0)
    )

    index_width = len(str(len(points) - 1)) if len(points) > 1 else 2
    for i, point in enumerate(points):
        ax.add_patch(
            patches.Rectangle(
                (point.x - margin_width, point.y - margin_height),
                2 * margin_width,
                2 * margin_height,
                edgecolor=_TABLEAU_PALETTE[i % len(_TABLEAU_PALETTE)],
                facecolor="none",
                linewidth=1.0,
                label=f"{label_prefix} {i:0{index_width}d}",
            )
        )

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_max, y_min)  # inverted: image y increases downward
    ax.set_xlabel("x (pixels)")
    ax.set_ylabel("y (pixels)")
    if points:
        ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=7)

    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def _reticle_marker_path(
    *,
    ring_radius: float = 0.85,
    tick_outer: float = 1.20,
    num_circle_points: int = 64,
) -> MarkerPath:
    """A target-reticle glyph: a ring with four tick marks poking through it.

    Built as a matplotlib marker path (unit-scaled to roughly [-1, 1]) meant
    to be *stroked*, not filled -- a circle outline, plus four short line
    segments along +/-x and +/-y running from the circle's own radius out
    past it, so the center stays fully open. Unlike a filled ring (an
    annulus), a stroked outline's thickness is set directly via
    `markeredgewidth` (in points), independent of this path's own geometry
    -- letting the line be pushed far thinner than a filled band can go
    before anti-aliasing makes it look patchy.

    Args:
        ring_radius: The circle's radius; also each tick's start radius.
        tick_outer: Each tick's end radius (past `ring_radius`).
        num_circle_points: Number of vertices approximating the circle.

    Returns:
        A compound `matplotlib.path.Path` usable as a `marker=` argument,
        with `markerfacecolor="none"` so only its stroke renders.
    """
    theta = np.linspace(0, 2 * np.pi, num_circle_points, endpoint=False)
    circle = np.column_stack((ring_radius * np.cos(theta), ring_radius * np.sin(theta)))
    # Path(..., closed=True) treats the *last* vertex as the ignored
    # CLOSEPOLY placeholder rather than drawing through it, so it must be a
    # repeat of the first vertex -- otherwise the final edge is dropped.
    circle_path = MarkerPath(np.vstack([circle, circle[:1]]), closed=True)

    tick_codes = [MarkerPath.MOVETO, MarkerPath.LINETO]
    tick_paths = [
        MarkerPath(
            [
                (direction_x * ring_radius, direction_y * ring_radius),
                (direction_x * tick_outer, direction_y * tick_outer),
            ],
            codes=tick_codes,
        )
        for direction_x, direction_y in [(1, 0), (-1, 0), (0, 1), (0, -1)]
    ]

    return MarkerPath.make_compound_path(circle_path, *tick_paths)


def point_grid_plot(
    *,
    image: np.ndarray,
    points: Sequence[PixelCoordinate],
    color: str = "red",
    show_node_numbers: bool = True,
    labels: Sequence[str] | None = None,
    dot_size: float | None = None,
    origin: PixelCoordinate = PixelCoordinate(x=0, y=0),
    circle_center: PixelCoordinate | None = None,
    circle_radius: float | None = None,
    circle_linewidth: float = 1.5,
    figsize: tuple[float, float] | None = None,
    path: Path,
    dpi: int = 300,
) -> None:
    """Save a figure marking each of `points` on `image`, labeled by its own index.

    Each point is drawn as a target-reticle glyph in `color` -- a ring with
    four tick marks poking through it, open at the center so the
    underlying image stays visible, plus a single-pixel dot at the point's
    exact location (where the N/S or E/W ticks would cross, if extended
    across the open center) -- with its position in `points` (its
    row-major index, e.g. from
    [`dictk.grid.generate`](../grid.html#generate)) as a short zero-padded
    label just up-right of the marker -- e.g. `points[0]` is labeled `"00"`,
    `points[19]` is labeled `"19"`, for a 20-point collection.

    Args:
        image: Source 2D grayscale image array.
        points: The points to mark, in the same reference frame as
            `origin` (by default, `image`'s own frame -- see `origin`
            below). May be empty (an unmarked copy of `image` is saved).
        color: Matplotlib color name for every marker and label.
        show_node_numbers: Whether to draw the reticle glyph and zero-padded
            index label described above. Default `True` matches every
            existing call site's own output exactly. `False` draws only
            the single-pixel center dot at each point -- a bare position
            marker with none of the reticle/label clutter, meant for a
            point count dense enough that a reticle-and-label per point
            would be unreadable (a few thousand points, not a dozen).
        labels: Optional label text per point, same length and order as
            `points`, overriding the default zero-padded `points`-local
            index. For a `points` list that's already a subset of some
            larger collection (e.g. every 4th point of a denser grid,
            picked to space labels legibly), this shows each point's
            *true* index in that larger collection instead of a
            re-enumerated `0, 1, 2, ...` that would otherwise misrepresent
            which points were skipped. Ignored when `show_node_numbers` is
            `False`.
        dot_size: Optional matplotlib `markersize` (in points) for the
            single-pixel center dot at each point's exact location.
            Default `None` keeps that dot exactly 1 raster pixel wide at
            `dpi` -- the same on-canvas size the reticle glyph's own
            center point has always used, appropriate when the reticle
            (or a label) is doing the actual work of marking a point.
            With `show_node_numbers=False`, the center dot is the *only*
            marker drawn, and 1 raster pixel is too faint to see clearly
            against real image content -- pass a larger value (e.g. `2`
            or `3`) to make it visible.
        origin: Where `image`'s own top-left corner sits in `points`'
            reference frame. Default `PixelCoordinate(x=0, y=0)` means
            `image` and `points` already share one frame -- every
            existing call site's own behavior, unchanged. Pass `image`'s
            true position (e.g. [`subimage`](./image.html#subimage)'s own
            `origin` argument) when `image` is a crop of some larger
            image and `points` are still expressed in that larger
            image's coordinates: the axes then read in the *larger*
            image's own numbers, not `image`'s local `0`-based ones, so
            the same point reads identically whether it's plotted here
            or in a figure of the uncropped image.
        circle_center: Optional center, in the same reference frame as
            `points`, of a red circle outline drawn on top of the image
            -- same style as
            [`spatial_correlation_quadrant_plot`](#spatial_correlation_quadrant_plot)'s
            own Solution Vicinity marker. Meant to visually tie a figure
            of one region back to a figure of a wider region it was
            cropped from: draw the same `circle_center`/`circle_radius`
            in both, and pick the radius to match the *narrower*
            figure's own extent (e.g. half its width) -- there, the
            circle exactly touches all four edges; in the wider figure,
            it appears as a normal circle marking exactly the region
            the narrower one shows. Must be given together with
            `circle_radius`.
        circle_radius: Radius, in the same units as `points`' own
            coordinates, of the circle described above. Must be given
            together with `circle_center`.
        circle_linewidth: Matplotlib `linewidth` for the circle outline
            above. Default `1.5` matches
            [`spatial_correlation_quadrant_plot`](#spatial_correlation_quadrant_plot)'s
            own circle exactly. Ignored when `circle_center` is `None`.
        figsize: Optional (width, height) in inches for the saved figure.
            By default the canvas is sized from `image`/`points`' own data
            extent; pass this to override with a fixed size instead.
        path: Output file path for the figure; format is inferred from the
            extension by matplotlib's savefig (e.g. .png), not dictk's own
            write/write_svg.
        dpi: Resolution of the saved figure.

    Raises:
        ValueError: If `labels` is given and its length doesn't match
            `points`, or if exactly one of `circle_center`/`circle_radius`
            is given without the other.
    """
    if (circle_center is None) != (circle_radius is None):
        raise ValueError("circle_center and circle_radius must be given together")
    if labels is not None and len(labels) != len(points):
        raise ValueError(
            f"labels has {len(labels)} entries, but points has {len(points)}"
        )
    image_height, image_width = image.shape
    image_left, image_top = origin.x, origin.y
    image_right, image_bottom = origin.x + image_width, origin.y + image_height

    endpoints_x = [point.x for point in points]
    endpoints_y = [point.y for point in points]
    margin = max(image_width, image_height) * 0.05
    # Small up-right offset for point labels, so label text doesn't sit
    # directly on top of its own marker -- same convention as point_plot().
    label_offset = max(image_width, image_height) * 0.03
    label_font_size = 12
    if points and show_node_numbers:
        label_text_height = label_font_size / 72 * _FIGURE_PIXELS_PER_INCH
        # Grow the margin uniformly (not just at the top) so a label above
        # the topmost point still has room, while all four margins match.
        # Capped at half the image's own size: label_text_height is a
        # fixed absolute constant (a fixed font size, not scaled to image
        # size), so on a small image/crop it would otherwise dominate the
        # whole canvas -- e.g. a 25x25px crop would demand a margin nearly
        # 3x wider than the image itself, mostly blank. The cap trades a
        # little label headroom on a very small image for a canvas that
        # still reads as "the image," not "mostly margin." No labels are
        # drawn at all when show_node_numbers is False, so this margin
        # isn't needed then either.
        label_margin = 2 * label_offset + label_text_height
        margin = max(margin, min(label_margin, max(image_width, image_height) * 0.5))
    x_min = min(image_left, *endpoints_x, image_left) - margin
    x_max = max(image_right, *endpoints_x, image_right) + margin
    y_min = min(image_top, *endpoints_y, image_top) - margin
    y_max = max(image_bottom, *endpoints_y, image_bottom) + margin
    label_outline = [patheffects.withStroke(linewidth=1, foreground="white")]

    if figsize is None:
        figsize = (
            (x_max - x_min) / _FIGURE_PIXELS_PER_INCH,
            (y_max - y_min) / _FIGURE_PIXELS_PER_INCH,
        )
    fig, ax = plt.subplots(figsize=figsize)
    ax.imshow(
        image,
        cmap="gray",
        origin="upper",
        extent=(image_left, image_right, image_bottom, image_top),
    )
    if circle_center is not None:
        ax.add_patch(
            patches.Circle(
                (circle_center.x, circle_center.y),
                radius=circle_radius,
                edgecolor="red",
                facecolor="none",
                linewidth=circle_linewidth,
            )
        )

    reticle = _reticle_marker_path()
    # A single-raster-pixel dot at each point's exact location: where the
    # reticle's N/S ticks (or E/W ticks), if extended across the open
    # center, would cross. markeredgewidth=0 is required -- otherwise the
    # default 1pt stroke dominates a marker this small and floors its
    # rendered size at several pixels regardless of markersize.
    center_dot_size = dot_size if dot_size is not None else 72 / dpi
    index_width = len(str(len(points) - 1)) if len(points) > 1 else 2
    point_labels = (
        labels
        if labels is not None
        else [f"{i:0{index_width}d}" for i in range(len(points))]
    )
    for i, point in enumerate(points):
        if show_node_numbers:
            ax.plot(
                point.x,
                point.y,
                marker=reticle,
                markerfacecolor="none",
                markeredgecolor=color,
                markeredgewidth=0.5,
                markersize=20,
            )
        ax.plot(
            point.x,
            point.y,
            marker="s",
            color=color,
            markersize=center_dot_size,
            markeredgewidth=0,
        )
        if show_node_numbers:
            ax.text(
                point.x + label_offset,
                point.y - label_offset,
                point_labels[i],
                color=color,
                fontsize=label_font_size,
                va="bottom",
                path_effects=label_outline,
            )

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_max, y_min)  # inverted: image y increases downward
    ax.set_xlabel("x (pixels)")
    ax.set_ylabel("y (pixels)")

    plt.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def element_strain_plot(
    *,
    points: Sequence[PixelCoordinate | SubpixelCoordinate],
    elements: Sequence[tuple[int, int, int, int]],
    coordinates: Sequence[tuple[float, float]],
    values: Sequence[float],
    label: str,
    image: np.ndarray | None = None,
    show_node_numbers: bool = False,
    show_mesh_lines: bool = True,
    cmap: str | Colormap = "viridis",
    dot_size: float = 150,
    marker: str = "o",
    vmin: float | None = None,
    vmax: float | None = None,
    figsize: tuple[float, float] = (10.0, 5.0),
    path: Path,
    dpi: int = 300,
) -> None:
    r"""Save a figure of a Q4 mesh with its Gauss points colored by a scalar value.

    Modeled on the reference `hdic` codebase's
    `~/hdic/src/hdic/types/fea_vis.py`'s `plot_strain_at_gauss_points` --
    same two-mode design (with or without a background image), same
    node-number/Gauss-point-scatter/colorbar layout -- adapted to dictk's
    own point/element representation
    ([`dictk.grid.elements`](../grid.html#elements),
    [`dictk.element.gauss_point_coordinates`](../element.html#gauss_point_coordinates)).
    Deliberately agnostic to which strain measure (or any other
    per-Gauss-point scalar) produced `values` -- it only draws what it's
    given, matching
    [`point_grid_plot`](#point_grid_plot)/[`point_grid_boxes_plot`](#point_grid_boxes_plot)'s
    own "just draws what it's given" design, rather than computing strain
    itself.

    Draws each of `elements`' 4-corner polygon outline from `points`
    (optionally, see `show_mesh_lines`), optionally labels each of
    `points` with its own zero-padded index
    (matching `point_grid_plot`'s exact `"00"`, `"01"`, ... convention),
    and scatters `coordinates` colored by `values` with a colorbar
    labeled `label`. If `image` is given, it's drawn as the background
    (e.g. pass the current/deformed image, with `points`/`coordinates` in
    that same current configuration, to show the mesh atop what it was
    measured from); otherwise the axes alone are y-inverted to match
    image/pixel convention (y increasing downward), so the two modes
    render in the same visual orientation. The axes are always
    aspect-locked 1:1 (a pixel spans the same rendered length along
    x and y), regardless of `figsize` or `image`'s own shape -- so the
    mesh's true proportions are never visually distorted.

    Args:
        points: The mesh's corner node positions, in the same
            configuration `coordinates` uses (e.g. `found`, not the
            original reference `points`, to draw the deformed shape).
        elements: Q4 connectivity, e.g. from
            [`dictk.grid.elements`](../grid.html#elements) -- each
            4-tuple indexes into `points`.
        coordinates: One `(X, Y)` position per Gauss point, e.g. from
            [`dictk.element.gauss_point_coordinates`](../element.html#gauss_point_coordinates)
            called once per element and concatenated, in the same order
            as `values`.
        values: One scalar per Gauss point, same order and length as
            `coordinates` -- e.g. a strain tensor's own `[0, 0]`
            component at each point. This function doesn't compute
            strain itself, so the caller picks the strain measure by
            choosing which function computed `values` --
            [`dictk.element.gauss_point_log_strains`](../element.html#gauss_point_log_strains)
            vs.
            [`dictk.element.gauss_point_green_lagrange_strains`](../element.html#gauss_point_green_lagrange_strains),
            for instance -- and should set `label` to match.
        label: Colorbar label, e.g. `r"Log Strain, $E_{11}$"`.
        image: Optional background image (2D grayscale array). Default
            `None` draws the mesh alone, on a plain y-inverted axes.
        show_node_numbers: Whether to label each of `points` with its own
            zero-padded index.
        show_mesh_lines: Whether to draw each element's own 4-corner
            outline. Default `True`. At high point density the mesh
            lines add visual clutter without much information -- a
            dense enough scatter (see `dot_size`) already reads as a
            field on its own; `False` drops the outlines so the
            colored points aren't fighting a grid of black lines for
            attention.
        cmap: Matplotlib colormap for the Gauss-point scatter -- either
            a name (e.g. `"viridis"`) or a `Colormap` instance (e.g.
            `matplotlib.colors.ListedColormap`, for a custom or
            externally-matched palette).
        dot_size: Marker size (matplotlib `scatter`'s own `s`) for each
            Gauss point. Default `150` suits sparse meshes; a dense mesh
            with points only a few pixels apart needs a smaller value, or
            neighboring markers overlap into a solid mass instead of a
            legible field.
        marker: Matplotlib marker style for each Gauss point. Default
            `"o"` (circle). On a regular grid dense enough that
            neighboring markers touch, circles leave small diamond-
            shaped gaps at their corners (tangent circles never fully
            tile a plane) -- `"s"` (square), sized and axis-aligned with
            the grid, tiles edge to edge with no gaps, reading as a
            genuinely continuous field rather than a field of dots.
        vmin: Optional fixed lower bound for the color scale. Default
            `None` auto-scales from `values`' own min, matching every
            existing call. Set alongside `vmax` to pin the colorbar to a
            specific range -- e.g. matching an external tool's own
            colorbar exactly, for a direct visual comparison between two
            figures that wouldn't otherwise share a color scale. Values
            outside `[vmin, vmax]` still plot, just clipped to the
            scale's own end colors, the same way matplotlib always
            handles an explicit `vmin`/`vmax`.
        vmax: Optional fixed upper bound for the color scale; see `vmin`.
        figsize: `(width, height)` in inches for the saved figure, used
            whether or not `image` is given -- unlike `point_grid_plot`,
            this isn't sized from `image`'s own shape (see `image`
            above).
        path: Output file path for the figure; format is inferred from
            the extension by matplotlib's savefig (e.g. `.png`).
        dpi: Resolution of the saved figure.
    """
    gauss_xs = [c[0] for c in coordinates]
    gauss_ys = [c[1] for c in coordinates]

    # Same figsize whether or not image is given -- not sized from
    # image.shape -- matching hdic's own plot_strain_at_gauss_points,
    # which uses one fixed canvas for both calls.
    fig, ax = plt.subplots(figsize=figsize)

    if image is not None:
        image_height, image_width = image.shape
        ax.imshow(
            image,
            cmap="gray",
            origin="upper",
            extent=(0, image_width, image_height, 0),
        )
    elif not ax.yaxis_inverted():
        # No image to establish the y-down orientation via its own
        # extent -- invert explicitly, matching hdic's own conditional
        # invert_yaxis() call.
        ax.invert_yaxis()

    if show_mesh_lines:
        for element in elements:
            corners = [points[i] for i in element]
            corners.append(corners[0])  # close the quadrilateral
            ax.plot([c.x for c in corners], [c.y for c in corners], "k-", alpha=0.3)

    if show_node_numbers:
        label_outline = [patheffects.withStroke(linewidth=1, foreground="white")]
        index_width = len(str(len(points) - 1)) if len(points) > 1 else 2
        for i, point in enumerate(points):
            ax.text(
                point.x,
                point.y,
                f"{i:0{index_width}d}",
                color="red",
                fontsize=10,
                fontweight="bold",
                ha="center",
                va="center",
                path_effects=label_outline,
            )

    scatter = ax.scatter(
        gauss_xs,
        gauss_ys,
        c=values,
        cmap=cmap,
        s=dot_size,
        marker=marker,
        vmin=vmin,
        vmax=vmax,
    )
    fig.colorbar(scatter, ax=ax, label=label)

    ax.axis("image")  # aspect-locked 1:1, autoscaled tight to the data --
    # matching hdic's own plt.axis("image") exactly, not a manually
    # recreated aspect+anchor+xlim/ylim equivalent.
    ax.set_xlabel("x (pixels)")
    ax.set_ylabel("y (pixels)")

    plt.tight_layout()
    # No bbox_inches="tight" here, unlike this module's other plot
    # functions -- matching hdic's own plot_strain_at_gauss_points, which
    # keeps its fixed-size canvas as saved (plt.savefig(..., dpi=300),
    # no bbox_inches) rather than cropping to the mesh's own, generally
    # smaller, content bounding box.
    plt.savefig(path, dpi=dpi)
    plt.close(fig)
