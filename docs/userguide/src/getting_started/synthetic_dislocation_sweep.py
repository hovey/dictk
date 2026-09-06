"""Sweep the crack_dislocation offset and check whether the correlation
surface's two-peak separation reliably encodes 2x that offset, for both
ZNCC (spatial) and phase correlation (FFT).
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

import dictk
from dictk.image import combine, crack_dislocation, subimage, PixelCoordinate
from dictk.correlation import zncc, phase_correlation

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

WIDTH = HEIGHT = 300
KERNEL_MARGIN = 25
OFFSETS = [1, 2, 3, 4, 6, 8, 12, 16, 20, 24, 28, 32]

speckle = dictk.rosta(width=WIDTH, height=HEIGHT, density=0.5)
photo = dictk.astronaut(width=WIDTH, height=HEIGHT)
reference_image = combine(a=speckle, b=photo)
p0 = PixelCoordinate(x=WIDTH // 2, y=HEIGHT // 2)


def two_peak_separation(surface: np.ndarray) -> tuple[int, int] | None:
    """Return (separation, count) for the two tallest peaks along the
    argmax column, or None if fewer than two are resolvable."""
    x_max = int(np.argmax(surface.max(axis=0)))
    column = surface[:, x_max]
    peaks, props = find_peaks(column, height=0.2 * column.max(), distance=2)
    if len(peaks) < 2:
        return None
    order = np.argsort(props["peak_heights"])[::-1][:2]
    y_top_two = sorted(peaks[order])
    return int(y_top_two[1] - y_top_two[0])


rows = []
for offset in OFFSETS:
    current_image = crack_dislocation(arr=reference_image, offset=float(offset))
    search_margin = KERNEL_MARGIN + int(np.ceil(offset)) + 10

    kernel = subimage(
        image=reference_image,
        origin=PixelCoordinate(x=p0.x - KERNEL_MARGIN, y=p0.y - KERNEL_MARGIN),
        width=2 * KERNEL_MARGIN,
        height=2 * KERNEL_MARGIN,
    )
    search = subimage(
        image=current_image,
        origin=PixelCoordinate(x=p0.x - search_margin, y=p0.y - search_margin),
        width=2 * search_margin,
        height=2 * search_margin,
    )

    zncc_sep = two_peak_separation(zncc(kernel=kernel, search=search))
    phase_sep = two_peak_separation(phase_correlation(kernel=kernel, search=search))
    rows.append((offset, zncc_sep, phase_sep))

print("| offset (px) | 2 x offset | ZNCC separation | ZNCC matches | Phase separation | Phase matches |")
print("|---|---|---|---|---|---|")
for offset, zncc_sep, phase_sep in rows:
    expected = 2 * offset
    print(
        f"| {offset} | {expected} | "
        f"{zncc_sep if zncc_sep is not None else 'n/a'} | "
        f"{zncc_sep == expected} | "
        f"{phase_sep if phase_sep is not None else 'n/a'} | "
        f"{phase_sep == expected} |"
    )

fig, ax = plt.subplots(figsize=(6.0, 5.0), constrained_layout=True)
offsets_plot = [r[0] for r in rows]
zncc_plot = [r[1] for r in rows]
phase_plot = [r[2] for r in rows]
line_x = np.linspace(0, max(offsets_plot), 100)
ax.plot(line_x, 2 * line_x, linestyle="--", color="black", linewidth=1, label="separation = 2 x offset")
ax.plot(offsets_plot, zncc_plot, marker="o", linestyle="none", color="tab:blue", label="ZNCC", markersize=8)
ax.plot(offsets_plot, phase_plot, marker="x", linestyle="none", color="tab:orange", label="Phase (FFT)", markersize=8)
ax.set_xlabel("crack_dislocation offset (pixels)")
ax.set_ylabel("peak separation (pixels)")
ax.set_title("Peak Separation vs. Dislocation Offset")
ax.legend()
fig.savefig("synthetic_dislocation_sweep.png", dpi=300)
print("Saved: synthetic_dislocation_sweep.png")
