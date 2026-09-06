"""Sweep the kernel window's center x position across the crack and
watch the two ZNCC peaks trade dominance: a single peak away from the
crack, both present and comparable near it.
"""

import matplotlib.pyplot as plt

import dictk
from dictk.image import combine, crack_dislocation, subimage, PixelCoordinate
from dictk.correlation import zncc

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

WIDTH = HEIGHT = 300
OFFSET = 4.0
KERNEL_MARGIN = 25
SEARCH_MARGIN = 45
Y = 150
CENTER_INDEX = SEARCH_MARGIN - KERNEL_MARGIN  # 20, the zero-shift index
LEFT_ROW = CENTER_INDEX + int(OFFSET)  # y=24, dy=+4 (left half's own shift)
RIGHT_ROW = CENTER_INDEX - int(OFFSET)  # y=16, dy=-4 (right half's own shift)

speckle = dictk.rosta(width=WIDTH, height=HEIGHT, density=0.5)
photo = dictk.astronaut(width=WIDTH, height=HEIGHT)
reference_image = combine(a=speckle, b=photo)
current_image = crack_dislocation(arr=reference_image, offset=OFFSET)

xs = list(range(100, 201))
left_peak = []
right_peak = []
for x in xs:
    p0 = PixelCoordinate(x=x, y=Y)
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
    surf = zncc(kernel=kernel, search=search)
    left_peak.append(surf[LEFT_ROW, CENTER_INDEX])
    right_peak.append(surf[RIGHT_ROW, CENTER_INDEX])

full_left_boundary = (
    WIDTH / 2 - KERNEL_MARGIN
)  # 125: kernel entirely left of the crack at or below this x
full_right_boundary = (
    WIDTH / 2 + KERNEL_MARGIN
)  # 175: kernel entirely right of the crack at or above this x

print("| kernel center x | left-half peak (dy=+4) | right-half peak (dy=-4) |")
print("|---|---|---|")
for x in range(100, 201, 10):
    i = xs.index(x)
    print(f"| {x} | {left_peak[i]:.3f} | {right_peak[i]:.3f} |")

fig, ax = plt.subplots(figsize=(7.0, 5.0), constrained_layout=True)
ax.plot(xs, left_peak, color="tab:blue", label="peak at Δy=+4 (left half's own shift)")
ax.plot(
    xs, right_peak, color="tab:orange", label="peak at Δy=-4 (right half's own shift)"
)
ax.axvline(full_left_boundary, color="black", linestyle=":", linewidth=1)
ax.axvline(full_right_boundary, color="black", linestyle=":", linewidth=1)
ax.axvline(WIDTH / 2, color="gray", linestyle="--", linewidth=1)
ax.set_xlabel("kernel window center x (pixels)")
ax.set_ylabel("ZNCC value")
ax.set_title("Peak Magnitudes vs. Window Center x")
ax.legend(loc="lower right")
fig.savefig("synthetic_dislocation_x_sweep.png", dpi=300)
print("Saved: synthetic_dislocation_x_sweep.png")
