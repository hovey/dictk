"""The same fractional-position error curve as
kernel_warping_pixel_locking.py, for both `grid.locate_subpixel` and
`grid.locate_warp`, on the same axes.
"""

import time

import matplotlib.pyplot as plt
import numpy as np

from dictk.grid import generate, locate_subpixel, locate_warp
from dictk.image import PixelCoordinate, read, stretch

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

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
kwargs = dict(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=13,
    kernel_margin_height=13,
    search_margin_width=25,
    search_margin_height=25,
)

true_x = np.array([p.x * FACTOR_X for p in points])
fraction = true_x % 1
bins = np.linspace(0, 1, 11)
centers = (bins[:-1] + bins[1:]) / 2

fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
print(
    "| Tracker | Time (s) | Mean $x$ error (px) | Std $x$ error (px) | Max \\|$x$ error\\| (px) |"
)
print("|---|---|---|---|---|")
for name, locate, extra, marker in [
    ("`locate_subpixel`", locate_subpixel, dict(upsample_factor=100), "o"),
    ("`locate_warp`", locate_warp, {}, "s"),
]:
    start = time.perf_counter()
    found = locate(**kwargs, **extra)
    elapsed = time.perf_counter() - start
    error_x = np.array([f.x for f in found]) - true_x
    print(
        f"| {name} | {elapsed:.1f} | {error_x.mean():+.4f} | {error_x.std():.4f} "
        f"| {np.abs(error_x).max():.4f} |"
    )
    means = [
        error_x[(fraction >= a) & (fraction < b)].mean() for a, b in zip(bins, bins[1:])
    ]
    ax.plot(centers, means, color="black", marker=marker, label=name.strip("`"))
ax.axhline(0, color="red", linestyle="--", linewidth=1)
ax.set_xlabel(r"fractional part of true $x$ (px)")
ax.set_ylabel(r"mean $x$ error (px)")
ax.legend(frameon=False)
fig.savefig("kernel_warping_bias.png", dpi=300)
