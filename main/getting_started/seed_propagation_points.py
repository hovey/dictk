"""The sweep's 30 points on `astronaut0` (left), and one point's own
deformation, pivoted on that point, then shifted (right).

Draws the same points and shifts as seed_propagation_baseline.py, from
the same seed. The close-up uses the point whose shift sits nearest the
median shift, so the example is typical, not hand-picked.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle
from scipy.ndimage import affine_transform

from dictk.image import read

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

MARGIN = 13
EDGE = 40
SAMPLE_COUNT = 30
# 15% stretch with 0.15 shear: inside the sweep, and large enough to see.
F = np.array([[1.15, 0.15], [0.0, 1.0]])
ZOOM = 30

reference_image = read(path="astronaut0.png")
height, width = reference_image.shape
rng = np.random.default_rng(0)
pivots = rng.integers(EDGE, 261, size=(SAMPLE_COUNT, 2)).astype(np.float64)
shifts = np.round(rng.uniform([4, 2], [8, 6], size=(SAMPLE_COUNT, 2)), 2)

typical = int(np.argmin(np.linalg.norm(shifts - np.median(shifts, axis=0), axis=1)))
pivot, shift = pivots[typical], shifts[typical]
inverse = np.linalg.inv(F)[::-1, ::-1]
offset = pivot[::-1] - inverse @ (pivot[::-1] + shift[::-1])
current_image = affine_transform(
    reference_image.astype(np.float64), inverse, offset=offset, order=5
)

square = np.array(
    [[-MARGIN, -MARGIN], [MARGIN, -MARGIN], [MARGIN, MARGIN], [-MARGIN, MARGIN]],
    dtype=np.float64,
)
deformed = square @ F.T

fig, (left, right) = plt.subplots(1, 2, figsize=(10, 5.2), constrained_layout=True)

left.imshow(reference_image, cmap="gray", vmin=0, vmax=255)
left.add_patch(
    Rectangle(
        (EDGE, EDGE),
        width - 1 - 2 * EDGE,
        height - 1 - 2 * EDGE,
        fill=False,
        edgecolor="white",
        linestyle="--",
        linewidth=1.5,
    )
)
others = np.delete(pivots, typical, axis=0)
left.scatter(*others.T, s=30, color="orange", edgecolor="black", linewidth=0.5)
left.scatter(*pivot, s=60, color="red", edgecolor="black", linewidth=0.5)
left.set_title(f"{SAMPLE_COUNT} reference points, at least {EDGE} px from each edge")
left.set_xlabel("x (pixels)")
left.set_ylabel("y (pixels)")

right.imshow(current_image, cmap="gray", vmin=0, vmax=255)
right.add_patch(
    Polygon(
        pivot + square,
        fill=False,
        edgecolor="white",
        linestyle="--",
        linewidth=1.5,
        label="reference kernel",
    )
)
right.add_patch(
    Polygon(
        pivot + deformed,
        fill=False,
        edgecolor="orange",
        linestyle=":",
        linewidth=2,
        label="deformed about the point",
    )
)
right.add_patch(
    Polygon(
        pivot + shift + deformed,
        fill=False,
        edgecolor="orange",
        linewidth=2,
        label="then shifted",
    )
)
right.annotate(
    "",
    xy=pivot + shift,
    xytext=pivot,
    arrowprops=dict(arrowstyle="-|>", color="orange", linewidth=2),
)
right.plot(*pivot, marker="o", color="red", markersize=7, mec="black")
right.plot(*(pivot + shift), marker="+", color="red", markersize=14, mew=2)
right.set_xlim(pivot[0] - ZOOM, pivot[0] + ZOOM + shift[0])
right.set_ylim(pivot[1] + ZOOM + shift[1], pivot[1] - ZOOM)
right.set_title(
    f"point ({pivot[0]:.0f}, {pivot[1]:.0f}), shift "
    f"({shift[0]:.2f}, {shift[1]:.2f}) px\n15% stretch, 0.15 shear"
)
right.set_xlabel("x (pixels)")
right.set_ylabel("y (pixels)")
right.legend(loc="lower left", fontsize=9, framealpha=0.85)

fig.savefig("seed_propagation_points.png", dpi=300)
