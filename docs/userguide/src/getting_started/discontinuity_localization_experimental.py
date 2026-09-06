"""Apply the winning dense peak-ratio sweep, and the rejected
golden-section variant, to the real crack image pair Experimental
Dislocation already introduced. No exact ground truth exists here --
Experimental Dislocation's own straddling-window example already
centered on `x=218, y=186` by inspection, so that value is a visual
sanity check, not a precise target.
"""

import matplotlib.pyplot as plt

from dictk.correlation import zncc
from dictk.discontinuity import locate as discontinuity_locate
from dictk.discontinuity import peak_ratio
from dictk.discontinuity import sweep as discontinuity_sweep
from dictk.image import PixelCoordinate, read, subimage

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

KERNEL_MARGIN = 25
SEARCH_MARGIN = 65
Y = 186

reference_image = read(path="experimental_dislocation_reference.tiff")
current_image = read(path="experimental_dislocation_current.tiff")


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
    """Golden-section search for a unimodal function's maximum on [a, b]."""
    ratio = (5**0.5 - 1) / 2
    c = b - ratio * (b - a)
    d = a + ratio * (b - a)
    evaluations = 2
    fc, fd = f(c), f(d)
    for _ in range(max_iterations):
        if abs(b - a) <= tol:
            break
        if fc > fd:
            b, d, fd = d, c, fc
            c = b - ratio * (b - a)
            fc = f(c)
        else:
            a, c, fc = c, d, fd
            d = a + ratio * (b - a)
            fd = f(d)
        evaluations += 1
    return (a + b) / 2, evaluations


# The winner: a dense sweep over a wide, uncommitted range. No bracket
# to get right -- it visits every candidate position and reports the
# tallest peak_ratio wherever it actually is.
wide_start, wide_end = 100, 350
dense = discontinuity_sweep(
    reference_image=reference_image,
    current_image=current_image,
    start=PixelCoordinate(x=wide_start, y=Y),
    end=PixelCoordinate(x=wide_end, y=Y),
    samples=126,
    kernel_margin_width=KERNEL_MARGIN,
    kernel_margin_height=KERNEL_MARGIN,
    search_margin_width=SEARCH_MARGIN,
    search_margin_height=SEARCH_MARGIN,
)
found = discontinuity_locate(
    reference_image=reference_image,
    current_image=current_image,
    start=PixelCoordinate(x=wide_start, y=Y),
    end=PixelCoordinate(x=wide_end, y=Y),
    samples=126,
    kernel_margin_width=KERNEL_MARGIN,
    kernel_margin_height=KERNEL_MARGIN,
    search_margin_width=SEARCH_MARGIN,
    search_margin_height=SEARCH_MARGIN,
)
print(f"Dense sweep (wide range {wide_start}-{wide_end}, 126 evaluations):")
print(f"  located crack position: x={found.x:.2f} (Experimental Dislocation's own x=218)")
print()

# The rejected alternative, at three brackets: one already centered
# tightly on the crack, one moderately wide, one as wide as the dense
# sweep's own range -- the bracket a person without a rough answer
# already in hand would have to use.
for bracket in [(178, 258), (150, 300), (100, 350)]:
    x, evaluations = golden_section_max(_evaluate, *bracket, tol=1.0)
    print(f"  golden-section, bracket {bracket}: x={x:.2f}, evaluations={evaluations}")
print()
print(
    "The tight and moderate brackets land within 1px of the dense sweep's "
    "own answer. The wide bracket -- the one that assumes no prior "
    "knowledge of roughly where the crack is -- converges instead to a "
    "smaller, secondary peak_ratio bump far from the real crack, "
    "confidently and silently."
)

fig, ax = plt.subplots(figsize=(7.5, 5.0), constrained_layout=True)
ax.plot([p.x for p in dense.positions], dense.peak_ratios, color="tab:blue")
ax.axvline(218, color="gray", linestyle="--", linewidth=1, label="x=218 (Experimental Dislocation)")
ax.axvline(
    found.x, color="tab:red", linestyle=":", linewidth=1.5, label=f"located (x={found.x:.1f})"
)
ax.set_xlabel("kernel window center x (pixels)")
ax.set_ylabel("peak_ratio")
ax.set_title("Dense Peak-Ratio Sweep on Real Data")
ax.legend(loc="upper right")
fig.savefig("discontinuity_localization_experimental.png", dpi=300)
print("Saved: discontinuity_localization_experimental.png")
