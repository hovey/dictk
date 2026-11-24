"""Measure how far t1 moves from t0 before choosing a search margin.
Tracks a coarse 8x7 grid of 200 px kernels, 200 px apart, with
`grid.locate`. A kernel that large holds hundreds of speckles, so its
whole-pixel match is reliable even with a wide search. Prints the range
of u and v.
"""

import numpy as np

from dictk.grid import generate, locate
from dictk.image import PixelCoordinate, read

reference_image = read(path="slip_example_t0.tiff")
current_image = read(path="slip_example_t1.tiff")

points = generate(
    origin=PixelCoordinate(x=150, y=150),
    count_x=8,
    count_y=7,
    spacing_x=200,
    spacing_y=200,
)
found = locate(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=100,
    kernel_margin_height=100,
    search_margin_width=120,
    search_margin_height=120,
)
u = np.array([f.x - p.x for f, p in zip(found, points)])
v = np.array([f.y - p.y for f, p in zip(found, points)])

print("| Points | u, min to max | v, min to max | Largest \\|u\\| or \\|v\\| |")
print("|---|---|---|---|")
print(
    f"| {len(points)} | {u.min()} to {u.max()} px | {v.min()} to {v.max()} px "
    f"| {max(np.abs(u).max(), np.abs(v).max())} px |"
)
