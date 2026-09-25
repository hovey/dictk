"""Pixel locking: `grid.locate_subpixel`'s own x-error against each
point's known true position, at High Point Density's full 53x54 grid.
Plots the error against the true position's fractional part, and along
one row of the grid.
"""

import matplotlib.pyplot as plt
import numpy as np

from dictk.grid import generate, locate_subpixel
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

true_x = np.array([p.x * FACTOR_X for p in points])
error_x = np.array([f.x for f in found]) - true_x
error_y = np.array([f.y - p.y for f, p in zip(found, points)])
fraction = true_x % 1

print(f"* x error: mean {error_x.mean():+.4f} px, std {error_x.std():.4f} px")
print(f"* y error: mean {error_y.mean():+.4f} px, std {error_y.std():.4f} px")

row = 27
rows = error_x.reshape(54, 53)
row_mean = rows.mean(axis=0)
correlations = [np.corrcoef(r, row_mean)[0, 1] for r in rows]
print()
print(
    f"Each row's x error vs. the all-row mean: correlation "
    f"{min(correlations):.2f} to {max(correlations):.2f}; "
    f"row {row} (y = {points[row * 53].y} px): {correlations[row]:.2f}"
)

bins = np.linspace(0, 1, 11)
centers = (bins[:-1] + bins[1:]) / 2
means = [
    error_x[(fraction >= a) & (fraction < b)].mean() for a, b in zip(bins, bins[1:])
]

fig, (left, right) = plt.subplots(1, 2, figsize=(10, 4), constrained_layout=True)
left.scatter(fraction, error_x, s=2, color="gray", alpha=0.4)
left.plot(centers, means, color="black", marker="o")
left.axhline(0, color="red", linestyle="--", linewidth=1)
left.set_xlabel(r"fractional part of true $x$ (px)")
left.set_ylabel(r"$x$ error (px)")

row_x = true_x.reshape(54, 53)[row]
right.plot(row_x, error_x.reshape(54, 53)[row], color="black", marker=".")
right.axhline(0, color="red", linestyle="--", linewidth=1)
for boundary in np.arange(np.ceil(row_x[0]), row_x[-1], 50 * FACTOR_X):
    right.axvline(boundary, color="gray", linestyle=":", linewidth=1)
right.set_xlabel(r"true $x$ (px)")
right.set_ylabel(r"$x$ error (px)")

fig.savefig("kernel_warping_pixel_locking.png", dpi=300)
print()
print("Saved: kernel_warping_pixel_locking.png")
