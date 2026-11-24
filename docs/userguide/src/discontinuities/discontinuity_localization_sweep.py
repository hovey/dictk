"""Locate the crack with a dense peak-ratio sweep and subpixel parabolic
refinement, no ground truth required -- `dictk.discontinuity.sweep()`
and `.locate()`, generalizing Synthetic Dislocation's own known-offset
x-sweep into a real detector.
"""

import matplotlib.pyplot as plt

import dictk
from dictk.discontinuity import locate, sweep
from dictk.image import PixelCoordinate, combine, crack_dislocation

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

WIDTH = HEIGHT = 300
OFFSET = 4.0
KERNEL_MARGIN = 25
SEARCH_MARGIN = 45
Y = 150
SAMPLES = 101

speckle = dictk.rosta(width=WIDTH, height=HEIGHT, density=0.5)
photo = dictk.astronaut(width=WIDTH, height=HEIGHT)
reference_image = combine(a=speckle, b=photo)
current_image = crack_dislocation(arr=reference_image, offset=OFFSET)

result = sweep(
    reference_image=reference_image,
    current_image=current_image,
    start=PixelCoordinate(x=100, y=Y),
    end=PixelCoordinate(x=200, y=Y),
    samples=SAMPLES,
    kernel_margin_width=KERNEL_MARGIN,
    kernel_margin_height=KERNEL_MARGIN,
    search_margin_width=SEARCH_MARGIN,
    search_margin_height=SEARCH_MARGIN,
)
xs = [p.x for p in result.positions]

found = locate(
    reference_image=reference_image,
    current_image=current_image,
    start=PixelCoordinate(x=100, y=Y),
    end=PixelCoordinate(x=200, y=Y),
    samples=SAMPLES,
    kernel_margin_width=KERNEL_MARGIN,
    kernel_margin_height=KERNEL_MARGIN,
    search_margin_width=SEARCH_MARGIN,
    search_margin_height=SEARCH_MARGIN,
)

print(f"Evaluations: {SAMPLES}")
print(f"Located crack position: x={found.x:.3f}")
print(f"Error vs. known x=150: {abs(found.x - 150):.3f}px")
print()

fig, ax = plt.subplots(figsize=(7.0, 5.0), constrained_layout=True)
ax.plot(xs, result.peak_ratios, color="tab:blue")
ax.axvline(150, color="gray", linestyle="--", linewidth=1, label="known crack (x=150)")
ax.axvline(
    found.x,
    color="tab:red",
    linestyle=":",
    linewidth=1.5,
    label=f"located crack (x={found.x:.1f})",
)
ax.set_xlabel("kernel window center x (pixels)")
ax.set_ylabel("peak_ratio")
ax.set_title("Dense Peak-Ratio Sweep")
ax.legend(loc="lower right")
fig.savefig("discontinuity_localization_sweep.png", dpi=300)
print("Saved: discontinuity_localization_sweep.png")
