"""Kernel Warping's tracked positions through a 15x15 strain window: a
summary table against the Q4 baseline, split into interior and
truncated windows.
"""

import numpy as np

from dictk.element import gauss_point_log_strains
from dictk.grid import elements, generate, locate_warp
from dictk.image import PixelCoordinate, read, stretch
from dictk.strain_window import log_strains

FACTOR_X = 1.02
COUNT_X, COUNT_Y = 53, 54
MARGIN = 7

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

q4 = np.array(
    [
        strain[0, 0]
        for element in elements(count_x=COUNT_X, count_y=COUNT_Y)
        for strain in gauss_point_log_strains(
            reference_points=[points[i] for i in element],
            current_points=[found[i] for i in element],
        )
    ]
)
window = log_strains(
    reference_points=points,
    current_points=found,
    count_x=COUNT_X,
    count_y=COUNT_Y,
    margin=MARGIN,
)[:, 0, 0]

i, j = np.meshgrid(np.arange(COUNT_X), np.arange(COUNT_Y))
interior = (
    (i >= MARGIN) & (i < COUNT_X - MARGIN) & (j >= MARGIN) & (j < COUNT_Y - MARGIN)
).ravel()

print("| Source | Points | Mean (µε) | Std (µε) | Min (µε) | Max (µε) |")
print("|---|---:|---:|---:|---:|---:|")
for name, values in [
    ("Q4, Gauss points", q4),
    ("15x15 window, all points", window),
    ("15x15 window, interior", window[interior]),
    ("15x15 window, truncated", window[~interior]),
]:
    values = values * 1e6
    print(
        f"| {name} | {values.size} | {values.mean():.0f} | {values.std():.0f} "
        f"| {values.min():.0f} | {values.max():.0f} |"
    )
print(f"| Analytical, $\\ln(1.02)$ | | {np.log(FACTOR_X) * 1e6:.0f} | 0 | | |")
