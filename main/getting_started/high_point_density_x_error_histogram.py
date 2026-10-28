"""Distribution of `grid.locate_subpixel`'s x error across High Point
Density's full 53x54 grid: the tracked x minus the true x = 1.02 X, with
the mean and one standard deviation marked.
"""

import matplotlib.pyplot as plt
import numpy as np

from dictk.grid import generate, locate_subpixel
from dictk.image import PixelCoordinate, read, stretch

FACTOR_X = 1.02

reference_image = read(path="astronaut0.png")
current_image = stretch(arr=reference_image, factor_x=FACTOR_X)
points = generate(
    origin=PixelCoordinate(x=18, y=16),
    count_x=53,
    count_y=54,
    spacing_x=5,
    spacing_y=5,
)
found = locate_subpixel(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=13,
    kernel_margin_height=13,
    search_margin_width=25,
    search_margin_height=25,
    upsample_factor=100,
)

error_x = np.array([f.x for f in found]) - np.array([p.x * FACTOR_X for p in points])
mean = error_x.mean()
std = error_x.std()
print(
    f"{len(points)} points: mean x error {mean:+.4f} px, std {std:.4f} px, "
    f"range [{error_x.min():+.2f}, {error_x.max():+.2f}] px"
)

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})
fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
ax.hist(error_x, bins=60, color="gray", alpha=0.8, label=r"$x$ error at 2862 points")
ax.axvspan(
    mean - std,
    mean + std,
    color="royalblue",
    alpha=0.15,
    label=rf"$\pm$ 1 standard deviation, {std:.4f} px",
)
ax.axvline(mean, color="black", linewidth=1.5, label=f"mean, {mean:+.4f} px")
ax.axvline(
    0,
    color="red",
    linestyle="--",
    linewidth=1.5,
    label="exact tracking, 0 px",
)
ax.set_xlabel(r"$x$ error (px)")
ax.set_ylabel("frequency")
ax.set_ylim(top=ax.get_ylim()[1] * 1.45)
legend = ax.legend(loc="upper right", framealpha=1.0)
legend.set_zorder(10)
fig.savefig("high_point_density_x_error_histogram.png", dpi=300)
