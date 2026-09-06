"""A faster alternative: instead of sweeping every position, search for
`peak_ratio`'s maximum with golden-section search, which needs only
O(log n) evaluations if the metric is unimodal within the search
bracket. Not shipped as library code -- see Applying It to Real Data for
why.
"""

import matplotlib.pyplot as plt
import numpy as np

import dictk
from dictk.correlation import zncc
from dictk.discontinuity import locate as discontinuity_locate
from dictk.discontinuity import peak_ratio
from dictk.discontinuity import sweep as discontinuity_sweep
from dictk.grid import generate
from dictk.grid import locate as grid_locate
from dictk.image import PixelCoordinate, combine, crack_dislocation, subimage

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

WIDTH = HEIGHT = 300
OFFSET = 4.0
KERNEL_MARGIN = 25
SEARCH_MARGIN = 45
Y = 150

speckle = dictk.rosta(width=WIDTH, height=HEIGHT, density=0.5)
photo = dictk.astronaut(width=WIDTH, height=HEIGHT)
reference_image = combine(a=speckle, b=photo)
current_image = crack_dislocation(arr=reference_image, offset=OFFSET)


def _evaluate(x):
    p0 = PixelCoordinate(x=int(round(x)), y=Y)
    kernel = subimage(
        image=reference_image,
        origin=PixelCoordinate(x=p0.x - KERNEL_MARGIN, y=p0.y - KERNEL_MARGIN),
        width=2 * KERNEL_MARGIN,
        height=2 * KERNEL_MARGIN,
    )
    search = subimage(
        image=current_image,
        origin=PixelCoordinate(x=p0.x - SEARCH_MARGIN, y=p0.y - SEARCH_MARGIN),
        width=2 * SEARCH_MARGIN,
        height=2 * SEARCH_MARGIN,
    )
    return peak_ratio(surface=zncc(kernel=kernel, search=search))


def golden_section_max(f, a, b, tol=1.0, max_iterations=50):
    """Golden-section search for a unimodal function's maximum on [a, b].

    Returns (x, evaluations, sampled_x) -- the found maximizer, how many
    times `f` was called, and every x actually sampled, in call order.
    """
    ratio = (5**0.5 - 1) / 2
    c = b - ratio * (b - a)
    d = a + ratio * (b - a)
    sampled = [c, d]
    fc, fd = f(c), f(d)
    for _ in range(max_iterations):
        if abs(b - a) <= tol:
            break
        if fc > fd:
            b, d, fd = d, c, fc
            c = b - ratio * (b - a)
            sampled.append(c)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + ratio * (b - a)
            sampled.append(d)
            fd = f(d)
    return (a + b) / 2, len(sampled), sampled


bisection_x, bisection_evaluations, bisection_samples = golden_section_max(
    _evaluate, 100, 200, tol=1.0
)
print(f"Golden-section result: x={bisection_x:.2f}, evaluations={bisection_evaluations}")
print(f"Error vs. known x=150: {abs(bisection_x - 150):.3f}px")
print()

# Full comparison, all three approaches, same synthetic dataset.
baseline_points = generate(
    origin=PixelCoordinate(x=100, y=Y), count_x=11, count_y=1, spacing_x=10, spacing_y=1
)
baseline_found = grid_locate(
    reference_image=reference_image,
    current_image=current_image,
    reference_points=baseline_points,
    kernel_margin_width=KERNEL_MARGIN,
    kernel_margin_height=KERNEL_MARGIN,
    search_margin_width=SEARCH_MARGIN,
    search_margin_height=SEARCH_MARGIN,
)
baseline_dy = [f.y - p.y for f, p in zip(baseline_found, baseline_points)]
baseline_jumps = [
    abs(baseline_dy[i + 1] - baseline_dy[i]) for i in range(len(baseline_dy) - 1)
]
baseline_i = int(np.argmax(baseline_jumps))
baseline_x = (baseline_points[baseline_i].x + baseline_points[baseline_i + 1].x) / 2

sweep_found = discontinuity_locate(
    reference_image=reference_image,
    current_image=current_image,
    start=PixelCoordinate(x=100, y=Y),
    end=PixelCoordinate(x=200, y=Y),
    samples=101,
    kernel_margin_width=KERNEL_MARGIN,
    kernel_margin_height=KERNEL_MARGIN,
    search_margin_width=SEARCH_MARGIN,
    search_margin_height=SEARCH_MARGIN,
)

print("| Approach | Evaluations | Localization Error (px) | Notes |")
print("|---|---|---|---|")
print(
    f"| Grid anomaly (baseline) | {len(baseline_points)} | "
    f"{abs(baseline_x - 150):.1f} | resolution capped at {10}px grid spacing |"
)
print(
    f"| Dense peak-ratio sweep (winner) | 101 | "
    f"{abs(sweep_found.x - 150):.3f} | robust to bracket width, see below |"
)
print(
    f"| Golden-section peak-ratio search | {bisection_evaluations} | "
    f"{abs(bisection_x - 150):.3f} | fast here, breaks on real data -- see below |"
)
print()

dense = discontinuity_sweep(
    reference_image=reference_image,
    current_image=current_image,
    start=PixelCoordinate(x=100, y=Y),
    end=PixelCoordinate(x=200, y=Y),
    samples=101,
    kernel_margin_width=KERNEL_MARGIN,
    kernel_margin_height=KERNEL_MARGIN,
    search_margin_width=SEARCH_MARGIN,
    search_margin_height=SEARCH_MARGIN,
)
fig, ax = plt.subplots(figsize=(7.0, 5.0), constrained_layout=True)
ax.plot(
    [p.x for p in dense.positions],
    dense.peak_ratios,
    color="tab:blue",
    linewidth=1,
    label="dense sweep (101 evaluations, for reference)",
)
ax.plot(
    bisection_samples,
    [_evaluate(x) for x in bisection_samples],
    marker="x",
    linestyle="none",
    color="tab:red",
    markersize=8,
    label=f"golden-section samples ({bisection_evaluations} evaluations)",
)
ax.axvline(150, color="gray", linestyle="--", linewidth=1)
ax.set_xlabel("kernel window center x (pixels)")
ax.set_ylabel("peak_ratio")
ax.set_title("Golden-Section Search vs. the Dense Sweep")
ax.legend(loc="lower right")
fig.savefig("discontinuity_localization_bisection.png", dpi=300)
print("Saved: discontinuity_localization_bisection.png")
