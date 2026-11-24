"""Track a 3x3 grid with `locate_warp` after flattening the reference
image around the first point, so that point's fit fails. Prints each
point's tracked position and error against the known motion, and
saves a two-panel figure of the kernels and the tracked motion.
"""

import warnings

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle

from dictk.grid import generate, locate_warp
from dictk.image import PixelCoordinate, translate
from dictk.rosta import rosta

# The whole-pixel stage warns that a flat kernel has no RMS error. The
# table reports the result, so the warning is noise.
warnings.filterwarnings("ignore", category=UserWarning)

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

DX, DY = -6, 8
KERNEL_MARGIN = 15
reference_image = rosta(width=150, height=150, density=0.4).astype(np.float64)
# A flat 41x41 patch holds the first point's whole 31x31 kernel.
reference_image[20:61, 20:61] = 0.0
current_image = translate(arr=reference_image, dx=DX, dy=DY)

points = generate(
    origin=PixelCoordinate(x=40, y=40),
    count_x=3,
    count_y=3,
    spacing_x=20,
    spacing_y=20,
)
found = locate_warp(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=KERNEL_MARGIN,
    kernel_margin_height=KERNEL_MARGIN,
    search_margin_width=30,
    search_margin_height=30,
)

print("| Reference point | Tracked x | Tracked y | Error |")
print("|---|---|---|---|")
for point, position in zip(points, found):
    error = np.hypot(position.x - (point.x + DX), position.y - (point.y + DY))
    print(
        f"| ({point.x}, {point.y}) | {position.x:.3f} | {position.y:.3f} "
        f"| {error:.3f} px |"
    )
lost = int(np.isnan([p.x for p in found]).sum())
print()
print(f"Failed fits: {lost} of {len(points)}")

fig, (reference_axis, current_axis) = plt.subplots(
    1, 2, figsize=(10.0, 5.2), constrained_layout=True
)
side = 2 * KERNEL_MARGIN + 1
# Two kernels are enough to compare: the failed one, and one tracked
# kernel that shares none of its pixels.
outlined = {(40, 40), (80, 80)}
for axis, image, title in (
    (reference_axis, reference_image, "(a) Reference image and kernels"),
    (current_axis, current_image, "(b) Current image and tracked motion"),
):
    axis.imshow(image, cmap="gray", vmin=0, vmax=255)
    axis.set_title(title)
    axis.set_xlabel("x (pixels)")
    axis.set_ylabel("y (pixels)")
    axis.set_xlim(0, 110)
    axis.set_ylim(110, 0)

for point, position in zip(points, found):
    failed = np.isnan(position.x)
    color = "tab:red" if failed else "tab:blue"
    if (point.x, point.y) in outlined:
        reference_axis.add_patch(
            Rectangle(
                (point.x - KERNEL_MARGIN - 0.5, point.y - KERNEL_MARGIN - 0.5),
                side,
                side,
                fill=False,
                edgecolor=color,
                linewidth=2.0,
                linestyle="--" if failed else "-",
            )
        )
    if failed:
        for axis, label in (
            (reference_axis, "flat kernel"),
            (current_axis, "fit failed: nan"),
        ):
            axis.plot(point.x, point.y, "x", color=color, markersize=10, mew=2.5)
            axis.annotate(
                label,
                (point.x, point.y),
                xytext=(0, 12),
                textcoords="offset points",
                ha="center",
                color="white",
                fontsize=10,
            )
    else:
        reference_axis.plot(point.x, point.y, "o", color=color, markersize=5)
        current_axis.annotate(
            "",
            xy=(position.x, position.y),
            xytext=(point.x, point.y),
            arrowprops=dict(arrowstyle="->", color=color, linewidth=1.5),
        )
        current_axis.plot(position.x, position.y, "o", color=color, markersize=5)
fig.savefig("kernel_warping_failed_fits.png", dpi=300)
