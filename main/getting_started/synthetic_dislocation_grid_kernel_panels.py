"""Show the two point grids from "VIC-2D-Style Point Density" side by
side over `reference_image`: the current 43x43 grid on the left, the
denser VIC-2D-style 53x54 grid on the right, each with a green box
around its own first point's kernel window -- 50x50 pixels for the
current grid's kernel_margin=25, 26x26 pixels for the VIC-2D-style
grid's kernel_margin=13. The box's own origin (green dot, labeled $K$)
and the tracked point at its center (orange dot, labeled $P$) match
"A Window Straddling the Crack"'s own labeling convention.
"""

import matplotlib.patches as patches
import matplotlib.patheffects as patheffects
import matplotlib.pyplot as plt

import dictk
from dictk.grid import generate
from dictk.image import PixelCoordinate, combine

WIDTH = HEIGHT = 300

speckle = dictk.rosta(width=WIDTH, height=HEIGHT, density=0.5)
photo = dictk.astronaut(width=WIDTH, height=HEIGHT)
reference_image = combine(a=speckle, b=photo)

CURRENT_KERNEL_MARGIN = 25
CURRENT_SEARCH_MARGIN = 45
points_current = generate(
    origin=PixelCoordinate(x=CURRENT_SEARCH_MARGIN, y=CURRENT_SEARCH_MARGIN),
    count_x=43,
    count_y=43,
    spacing_x=5,
    spacing_y=5,
)

VIC2D_STYLE_KERNEL_MARGIN = 13
VIC2D_STYLE_SEARCH_MARGIN = 25
points_vic2d = generate(
    origin=PixelCoordinate(x=18, y=16),
    count_x=53,
    count_y=54,
    spacing_x=5,
    spacing_y=5,
)

PANELS = [
    ("Current: 43x43, kernel_margin=25", points_current, CURRENT_KERNEL_MARGIN),
    ("VIC-2D-style: 53x54, kernel_margin=13", points_vic2d, VIC2D_STYLE_KERNEL_MARGIN),
]

LABEL_OFFSET = 6
LABEL_OUTLINE = [patheffects.withStroke(linewidth=2, foreground="white")]

fig, axes = plt.subplots(1, 2, figsize=(11.0, 5.5), constrained_layout=True)
for ax, (title, points, kernel_margin) in zip(axes, PANELS):
    ax.imshow(
        reference_image,
        cmap="gray",
        origin="upper",
        extent=(0, WIDTH, HEIGHT, 0),
    )
    ax.plot(
        [p.x for p in points],
        [p.y for p in points],
        marker="s",
        markersize=2.5,
        markeredgewidth=0,
        color="tab:orange",
        linestyle="none",
    )
    p0 = points[0]
    origin = PixelCoordinate(x=p0.x - kernel_margin, y=p0.y - kernel_margin)
    ax.add_patch(
        patches.Rectangle(
            (origin.x, origin.y),
            2 * kernel_margin,
            2 * kernel_margin,
            edgecolor="green",
            facecolor="none",
            linewidth=2.5,
        )
    )
    ax.plot(origin.x, origin.y, marker="o", color="green", markersize=8)
    ax.text(
        origin.x + LABEL_OFFSET,
        origin.y - LABEL_OFFSET,
        "$K$",
        color="green",
        fontsize=14,
        va="bottom",
        path_effects=LABEL_OUTLINE,
    )
    ax.plot(p0.x, p0.y, marker="o", color="tab:orange", markersize=7)
    ax.text(
        p0.x + LABEL_OFFSET,
        p0.y - LABEL_OFFSET,
        "$P$",
        color="tab:orange",
        fontsize=14,
        va="bottom",
        path_effects=LABEL_OUTLINE,
    )
    # A little headroom above y=0 so the $K$ label (which can land right
    # at the image's own top edge, depending on the grid's origin) never
    # collides with the panel's title.
    ax.set_xlim(0, WIDTH)
    ax.set_ylim(HEIGHT, -20)
    ax.set_xlabel("x (pixels)")
    ax.set_title(f"{title} (n={len(points)})")

axes[0].set_ylabel("y (pixels)")

fig.savefig("synthetic_dislocation_grid_kernel_panels.png", dpi=300)
print("Saved: synthetic_dislocation_grid_kernel_panels.png")
