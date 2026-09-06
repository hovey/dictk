"""A naive baseline: run standard single-peak DIC across the crack,
ignoring it, and look for a jump in the recovered displacement field
between neighboring grid points. Zero new library code -- entirely
`dictk.grid.generate`/`dictk.grid.locate`.
"""

import matplotlib.pyplot as plt
import numpy as np

import dictk
from dictk.grid import generate, locate
from dictk.image import PixelCoordinate, combine, crack_dislocation

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

WIDTH = HEIGHT = 300
OFFSET = 4.0
KERNEL_MARGIN = 25
SEARCH_MARGIN = 45
Y = 150
SPACING = 10

speckle = dictk.rosta(width=WIDTH, height=HEIGHT, density=0.5)
photo = dictk.astronaut(width=WIDTH, height=HEIGHT)
reference_image = combine(a=speckle, b=photo)
current_image = crack_dislocation(arr=reference_image, offset=OFFSET)

points = generate(
    origin=PixelCoordinate(x=100, y=Y), count_x=11, count_y=1, spacing_x=SPACING, spacing_y=1
)
found = locate(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=points,
    kernel_margin_width=KERNEL_MARGIN,
    kernel_margin_height=KERNEL_MARGIN,
    search_margin_width=SEARCH_MARGIN,
    search_margin_height=SEARCH_MARGIN,
)
displacements = [f.y - p.y for f, p in zip(found, points)]
jumps = [abs(displacements[i + 1] - displacements[i]) for i in range(len(displacements) - 1)]
jump_index = int(np.argmax(jumps))
crack_estimate = (points[jump_index].x + points[jump_index + 1].x) / 2

print(f"Grid spacing: {SPACING} px, {len(points)} points, {len(points)} correlation evaluations")
print(f"Largest displacement jump: {points[jump_index].x} -> {points[jump_index + 1].x}px")
print(f"Estimated crack position: x={crack_estimate}")
print(f"Error vs. known x=150: {abs(crack_estimate - 150)}px")
print()

fig, ax = plt.subplots(figsize=(6.0, 4.5), constrained_layout=True)
xs = [p.x for p in points]
ax.step(xs, displacements, where="mid", color="tab:blue", marker="o")
ax.axvline(150, color="gray", linestyle="--", linewidth=1, label="known crack (x=150)")
ax.axvline(
    crack_estimate,
    color="tab:red",
    linestyle=":",
    linewidth=1.5,
    label=f"estimated crack (x={crack_estimate:.0f})",
)
ax.set_xlabel("grid point x (pixels)")
ax.set_ylabel("recovered y-displacement (pixels)")
ax.set_title("Grid-Anomaly Baseline: Displacement Jump")
ax.legend(loc="center right")
fig.savefig("discontinuity_localization_baseline.png", dpi=300)
print("Saved: discontinuity_localization_baseline.png")
