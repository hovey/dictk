"""Kernel Warping's Q4 strain field next to the 15x15 strain window's
field, both on VIC-2D's own colorbar over the current image.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

from dictk.element import gauss_point_coordinates, gauss_point_log_strains
from dictk.grid import elements, generate, locate_warp
from dictk.image import PixelCoordinate, read, stretch
from dictk.strain_window import log_strains

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

FACTOR_X = 1.02
COUNT_X, COUNT_Y = 53, 54
MARGIN = 7
VMIN, VMAX = 17560, 22360

reference_image = read(path="astronaut0.png")
current_image = stretch(arr=reference_image, factor_x=FACTOR_X)
points = generate(
    origin=PixelCoordinate(x=18, y=16),
    count_x=COUNT_X,
    count_y=COUNT_Y,
    spacing_x=5,
    spacing_y=5,
)
found = locate_warp(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=13,
    kernel_margin_height=13,
    search_margin_width=25,
    search_margin_height=25,
)

q4_values, q4_coordinates = [], []
for element in elements(count_x=COUNT_X, count_y=COUNT_Y):
    corners = [found[i] for i in element]
    q4_values.extend(
        strain[0, 0]
        for strain in gauss_point_log_strains(
            reference_points=[points[i] for i in element],
            current_points=corners,
        )
    )
    q4_coordinates.extend(gauss_point_coordinates(points=corners))
q4_values = np.array(q4_values) * 1e6
q4_coordinates = np.array(q4_coordinates)
window_values = (
    log_strains(
        reference_points=points,
        current_points=found,
        count_x=COUNT_X,
        count_y=COUNT_Y,
        margin=MARGIN,
    )[:, 0, 0]
    * 1e6
)
window_coordinates = np.array([[p.x, p.y] for p in found])

vic2d_cmap = ListedColormap(
    [
        (0.8314, 0.0000, 1.0000),
        (0.5176, 0.0000, 1.0000),
        (0.1843, 0.0000, 1.0000),
        (0.0000, 0.1333, 1.0000),
        (0.0000, 0.4510, 1.0000),
        (0.0000, 0.7843, 1.0000),
        (0.0000, 1.0000, 0.8980),
        (0.0000, 1.0000, 0.5843),
        (0.0000, 1.0000, 0.2510),
        (0.0667, 1.0000, 0.0000),
        (0.3843, 1.0000, 0.0000),
        (0.7176, 1.0000, 0.0000),
        (1.0000, 0.9686, 0.0000),
        (1.0000, 0.6510, 0.0000),
        (1.0000, 0.3176, 0.0000),
        (1.0000, 0.0000, 0.0000),
    ]
)
band = (VMAX - VMIN) / vic2d_cmap.N

print("| Source | Inside colorbar | Bands touched |")
print("|---|---:|---:|")
for name, values in [
    ("`locate_warp` + Q4", q4_values),
    ("`locate_warp` + 15x15 window", window_values),
]:
    inside = np.mean((values >= VMIN) & (values <= VMAX)) * 100
    bands = np.unique(
        np.clip(((values - VMIN) // band).astype(int), 0, vic2d_cmap.N - 1)
    )
    print(f"| {name} | {inside:.1f}% | {bands.size} of {vic2d_cmap.N} |")
print()
print(f"Each colorbar band spans {band:.0f} microstrain.")

fig, axes = plt.subplots(1, 2, figsize=(11, 5.2), constrained_layout=True)
image_height, image_width = current_image.shape
for ax, coordinates, values, title in [
    (axes[0], q4_coordinates, q4_values, "(a) Q4 elements, 11024 Gauss points"),
    (axes[1], window_coordinates, window_values, "(b) 15x15 window, 2862 points"),
]:
    ax.imshow(
        current_image,
        cmap="gray",
        origin="upper",
        extent=(0, image_width, image_height, 0),
    )
    scatter = ax.scatter(
        coordinates[:, 0],
        coordinates[:, 1],
        c=values,
        cmap=vic2d_cmap,
        s=6 if values is q4_values else 24,
        marker="s",
        vmin=VMIN,
        vmax=VMAX,
    )
    ax.axis("image")
    ax.set_xlim(coordinates[:, 0].min() - 8, coordinates[:, 0].max() + 8)
    ax.set_ylim(coordinates[:, 1].max() + 8, coordinates[:, 1].min() - 8)
    ax.set_title(title)
    ax.set_xlabel("$x$ (px)")
axes[0].set_ylabel("$y$ (px)")
fig.colorbar(
    scatter,
    ax=axes,
    label=r"Log Strain, $E_{11}$ (microstrain)",
    shrink=0.85,
)
fig.savefig("strain_window_field.png", dpi=300)
